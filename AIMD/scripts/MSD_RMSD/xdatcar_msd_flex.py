#!/usr/bin/env python3
"""
xdatcar_msd_flex.py — XDATCAR 一体化 MSD/RMSD 计算与绘图

dt 默认自 AIMD/INCAR 的 POTIM；可选写 <A>/msd_data.dat 并 mv 汇总。
默认若出图：png mv 到 MSD_png/。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from bootstrap import init_imports

init_imports()

from path_config import add_work_root_argument, resolve_work_root
from msd_common import (
    aimd_dir_of,
    compute_msd_by_element,
    ensure_result_dirs,
    local_dat_path,
    publish_dat,
    publish_png,
    read_xdatcar,
    resolve_dt,
    results_to_table,
    system_dir_from_xdatcar,
    unique_elements,
    write_dat,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute and optionally plot MSD/RMSD from XDATCAR."
    )
    parser.add_argument("xdatcar", nargs="?", default="XDATCAR", help="Path to XDATCAR")
    parser.add_argument(
        "--dt",
        type=float,
        default=None,
        help="Timestep fs (default: POTIM from AIMD/INCAR)",
    )
    parser.add_argument("--elements", nargs="*", default=None)
    parser.add_argument(
        "--element-order", choices=("file", "alpha"), default="file"
    )
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument(
        "--write-dat",
        action="store_true",
        help="Also write <A>/msd_data.dat and publish to MSD_data_for_origin/",
    )
    parser.add_argument("--stride", type=int, default=100)
    parser.add_argument("-o", "--output", default=None, help="Temp png before mv")
    parser.add_argument("--keep-local", action="store_true")
    parser.add_argument("--no-publish", action="store_true")
    add_work_root_argument(parser)
    return parser


def plot_msd(results, save_path: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    for i, (elem, (t_ps, msd, rmsd)) in enumerate(results.items()):
        color = plt.cm.tab10(i % 10)
        ax1.plot(t_ps, msd, color=color, lw=1.5, label=elem)
        ax2.plot(t_ps, rmsd, color=color, lw=1.5, label=elem)

    for ax in (ax1, ax2):
        ax.legend(fontsize=9)
        ax.set_xlabel("Time (ps)")
        ax.grid(alpha=0.3)

    ax1.set_ylabel("MSD (A^2)")
    ax1.set_title("MSD")
    ax2.set_ylabel("RMSD (A)")
    ax2.set_title("RMSD")
    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=200)
    print(f"Plot saved: {save_path}")
    plt.close()


def print_summary(results, n_frames: int) -> None:
    elems = list(results.keys())
    sample_idx = [0, 500, 1000, 2000, 5000, 10000, 20000, 30000, n_frames - 1]
    hdr = f"{'Time(ps)':>10s}" + "".join(f"  {e}_MSD  {e}_RMSD" for e in elems)
    print("\n" + hdr)
    for i in sample_idx:
        if i >= n_frames:
            continue
        t = results[elems[0]][0][i]
        row = f"{t:10.2f}" + "".join(
            f"  {results[e][1][i]:8.4f}  {results[e][2][i]:6.4f}" for e in elems
        )
        print(row)
    print()
    for elem in elems:
        rmsd_end = results[elem][2][-1]
        if rmsd_end < 0.5:
            status = "stable"
        elif rmsd_end < 2.0:
            status = "warning"
        else:
            status = "diffusion"
        print(f"  {elem}: RMSD end = {rmsd_end:.4f} A -> {status}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    xdat = Path(args.xdatcar)
    system_dir = system_dir_from_xdatcar(xdat)
    system_a = system_dir.name
    work_root = (
        resolve_work_root(args.work_root)
        if args.work_root
        else system_dir.parent
    )

    try:
        timestep, dt_src = resolve_dt(aimd_dir_of(system_dir), cli_dt=args.dt)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"dt: {timestep} fs ({dt_src})")
    positions, elem_map = read_xdatcar(xdat)
    elements = args.elements or unique_elements(elem_map, order=args.element_order)
    print(
        f"XDATCAR: {xdat}\n"
        f"frames: {positions.shape[0]}, atoms: {positions.shape[1]}\n"
        f"elements: {elements}"
    )

    results = compute_msd_by_element(
        positions, timestep, elem_map, elements=elements
    )
    print_summary(results, positions.shape[0])

    if args.write_dat:
        local = local_dat_path(system_dir)
        write_dat(
            results_to_table(results), local, stride=args.stride, element_order=elements
        )
        if not args.no_publish:
            ensure_result_dirs(work_root)
            publish_dat(local, work_root, system_a, keep_local=args.keep_local)

    if not args.no_plot:
        tmp = (
            Path(args.output)
            if args.output
            else system_dir / f"{system_a}_tmp_msd_rmsd.png"
        )
        plot_msd(results, str(tmp))
        if not args.no_publish:
            ensure_result_dirs(work_root)
            publish_png(tmp, work_root, system_a, keep_local=args.keep_local)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
