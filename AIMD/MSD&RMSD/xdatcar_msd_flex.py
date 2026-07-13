#!/usr/bin/env python3
"""
xdatcar_msd_flex.py — XDATCAR 一体化 MSD/RMSD 计算与绘图

用途:
  一步完成：读取 XDATCAR → 按元素计算 MSD/RMSD → 打印摘要 → 出图。
  元素种类自动识别，换体系无需改脚本。

依赖:
  pip install numpy matplotlib

基本用法:
  python xdatcar_msd_flex.py XDATCAR
  python xdatcar_msd_flex.py path/to/XDATCAR --dt 1.0
  python xdatcar_msd_flex.py XDATCAR --no-plot          # 只计算，不画图
  python xdatcar_msd_flex.py XDATCAR --elements H Ag     # 只分析部分元素

常用参数:
  xdatcar              XDATCAR 路径（默认: XDATCAR）
  --dt                 AIMD 步长，单位 fs（默认: 1.0）
  -o, --output         输出图片路径（默认: <文件名>_msd_rmsd.png）
  --elements           指定要分析的元素（默认: 全部）
  --element-order      元素排序: file 或 alpha（默认: file）
  --no-plot            跳过绘图，仅打印数值摘要

与 extract_msd_flex.py 的区别:
  本脚本直接出图；若需 .dat 中间文件供后续自定义绘图，请用 extract_msd_flex.py。
"""
from __future__ import annotations

import argparse
import os
import sys

from msd_common import compute_msd_by_element, read_xdatcar, unique_elements


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute and optionally plot MSD/RMSD from XDATCAR."
    )
    parser.add_argument(
        "xdatcar",
        nargs="?",
        default="XDATCAR",
        help="Path to XDATCAR (default: XDATCAR)",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=1.0,
        help="AIMD timestep in fs (default: 1.0)",
    )
    parser.add_argument(
        "--elements",
        nargs="*",
        default=None,
        help="Only include selected elements (default: all in XDATCAR)",
    )
    parser.add_argument(
        "--element-order",
        choices=("file", "alpha"),
        default="file",
        help="Element ordering (default: file)",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip plotting and only print summary",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output image path (default: <xdatcar_basename>_msd_rmsd.png)",
    )
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
    plt.savefig(save_path, dpi=200)
    print(f"Plot saved: {save_path}")
    plt.close()


def print_summary(results, n_frames: int) -> None:
    elems = list(results.keys())
    sample_idx = [0, 500, 1000, 2000, 5000, 10000, 20000, 30000, n_frames - 1]
    hdr = f"{'Time(ps)':>10s}" + "".join(
        f"  {e}_MSD  {e}_RMSD" for e in elems
    )
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
    base = os.path.splitext(os.path.basename(args.xdatcar))[0]
    output = args.output or f"{base}_msd_rmsd.png"

    positions, elem_map = read_xdatcar(args.xdatcar)
    elements = args.elements or unique_elements(elem_map, order=args.element_order)

    print(
        f"XDATCAR: {args.xdatcar}\n"
        f"frames: {positions.shape[0]}, atoms: {positions.shape[1]}\n"
        f"elements in file: {unique_elements(elem_map, order='file')}\n"
        f"elements analyzed: {elements}"
    )

    results = compute_msd_by_element(
        positions, args.dt, elem_map, elements=elements
    )
    print_summary(results, positions.shape[0])

    if not args.no_plot:
        plot_msd(results, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
