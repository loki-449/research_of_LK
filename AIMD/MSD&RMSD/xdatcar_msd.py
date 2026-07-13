#!/usr/bin/env python3
"""MSD/RMSD from VASP XDATCAR - per element, time in ps"""
import numpy as np, sys, os

def read_xdatcar(path):
    with open(path) as f:
        lines = f.readlines()
    scale = float(lines[1].strip())
    lattice = np.array([list(map(float, l.split())) for l in lines[2:5]]) * scale
    elements_raw = lines[5].split()
    counts = list(map(int, lines[6].split()))
    n_atoms = sum(counts)
    elem_map = []
    for e, c in zip(elements_raw, counts):
        elem_map.extend([e] * c)
    frames = []
    idx = 7
    while idx < len(lines):
        ll = lines[idx].strip().lower()
        if ll.startswith(('direct', 'cart')):
            kw = lines[idx].strip()
            idx += 1
            coords = []
            for _ in range(n_atoms):
                if idx >= len(lines): break
                coords.append([float(x) for x in lines[idx].split()[:3]])
                idx += 1
            pos = np.array(coords)
            if kw.lower().startswith('direct'):
                pos = pos @ lattice
            frames.append(pos)
        else:
            idx += 1
    if not frames:
        raise ValueError("no frames in XDATCAR")
    return np.array(frames), elem_map

def compute_msd(positions, timestep_fs, elem_map):
    n_steps, n_atoms, _ = positions.shape
    t_ps = np.arange(n_steps) * timestep_fs / 1000.0
    results = {}
    for elem in sorted(set(elem_map)):
        idxs = [i for i,e in enumerate(elem_map) if e==elem]
        sub = positions[:, idxs, :]
        ref = sub[0]
        msd = np.zeros(n_steps)
        for t in range(n_steps):
            msd[t] = np.mean(np.sum((sub[t]-ref)**2, axis=1))
        results[elem] = (t_ps.copy(), msd, np.sqrt(msd))
    return results

def plot_msd(results, label, save_path):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    for i, (elem, (t, msd, rmsd)) in enumerate(results.items()):
        c = plt.cm.tab10(i % 10)
        ax1.plot(t, msd, color=c, lw=1, label=elem)
        ax2.plot(t, rmsd, color=c, lw=1, label=elem)
    for ax in (ax1, ax2):
        ax.legend(fontsize=8); ax.set_xlabel('Time (ps)'); ax.grid(alpha=0.3)
    ax1.set_ylabel('MSD (A^2)'); ax1.set_title('MSD')
    ax2.set_ylabel('RMSD (A)'); ax2.set_title('RMSD')
    plt.tight_layout(); plt.savefig(save_path or 'msd_rmsd.png', dpi=150)
    print(f"  chart: {save_path}"); plt.close()

if __name__ == '__main__':
    xd = sys.argv[1] if len(sys.argv)>1 else 'XDATCAR'
    dt = float(sys.argv[2]) if len(sys.argv)>2 else 1.0
    pos, em = read_xdatcar(xd)
    print(f"frames: {pos.shape[0]}, atoms: {pos.shape[1]}, elements: {sorted(set(em))}")
    res = compute_msd(pos, dt, em)
    # table
    elems = sorted(res.keys())
    hdr = f"{'Time(ps)':>10s}" + ''.join(f"  {e}_MSD  {e}_RMSD" for e in elems)
    print('\n'+hdr)
    for i in [0,500,1000,2000,5000,10000,20000,30000,pos.shape[0]-1]:
        if i>=pos.shape[0]: continue
        t = res[elems[0]][0][i]
        row = f"{t:10.2f}" + ''.join(f"  {res[e][1][i]:8.4f}  {res[e][2][i]:6.4f}" for e in elems)
        print(row)
    print()
    for e in elems:
        r = res[e][2][-1]
        s = "stable" if r<0.5 else ("warning" if r<2.0 else "diffusion")
        print(f"  {e}: RMSD end = {r:.4f} A -> {s}")
    out = os.path.splitext(xd)[0]
    plot_msd(res, out, f"{out}_msd_rmsd.png")
