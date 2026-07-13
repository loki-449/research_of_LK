#!/usr/bin/env python3
"""从 XDATCAR 提取 MSD/RMSD 数据，输出 .dat 表格文件"""
import numpy as np, sys

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
    return np.array(frames), elem_map

def compute_all_msd(positions, timestep_fs, elem_map):
    n_steps = positions.shape[0]
    t_ps = np.arange(n_steps) * timestep_fs / 1000.0
    data = {}
    for elem in sorted(set(elem_map)):
        idxs = [i for i,e in enumerate(elem_map) if e==elem]
        sub = positions[:, idxs, :]
        ref = sub[0]
        msd = np.array([np.mean(np.sum((sub[t]-ref)**2, axis=1)) for t in range(n_steps)])
        data[f'{elem}_MSD'] = msd
        data[f'{elem}_RMSD'] = np.sqrt(msd)
    data['Time_ps'] = t_ps
    return data

def write_dat(data, outpath, stride=100):
    """输出 .dat 表格，默认每100步写一行"""
    elems = [k.replace('_MSD','') for k in data if k.endswith('_MSD')]
    with open(outpath, 'w') as f:
        cols = ['Time(ps)'] + [f'{e}_MSD(A2)' for e in elems] + [f'{e}_RMSD(A)' for e in elems]
        f.write('# ' + '  '.join(f'{c:>12s}' for c in cols) + '\n')
        n = len(data['Time_ps'])
        for i in range(0, n, stride):
            vals = [data['Time_ps'][i]] + [data[f'{e}_MSD'][i] for e in elems] + [data[f'{e}_RMSD'][i] for e in elems]
            f.write('  '.join(f'{v:12.6f}' for v in vals) + '\n')
    print(f'Data written to {outpath} ({n//stride+1} rows, {len(elems)} elements)')

if __name__ == '__main__':
    xd = sys.argv[1] if len(sys.argv)>1 else 'XDATCAR'
    dt = float(sys.argv[2]) if len(sys.argv)>2 else 1.0
    out = sys.argv[3] if len(sys.argv)>3 else 'msd_data.dat'
    stride = int(sys.argv[4]) if len(sys.argv)>4 else 100

    pos, em = read_xdatcar(xd)
    print(f"frames: {pos.shape[0]}, atoms: {pos.shape[1]}, elements: {sorted(set(em))}")
    data = compute_all_msd(pos, dt, em)
    write_dat(data, out, stride)
