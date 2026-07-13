#!/usr/bin/env python3
"""
extract_msd_flex.py — 从 XDATCAR 提取 MSD/RMSD 数据（元素自动识别）

用途:
  读取任意 VASP XDATCAR，按元素拆分 MSD/RMSD，输出 .dat 表格文件。
  更换 XDATCAR 后无需修改脚本，元素种类自动从文件头读取。

依赖:
  pip install numpy

基本用法:
  python extract_msd_flex.py XDATCAR
  python extract_msd_flex.py path/to/XDATCAR --dt 1.0 -o msd_data.dat
  python extract_msd_flex.py XDATCAR --stride 100

常用参数:
  xdatcar              XDATCAR 路径（默认: XDATCAR）
  --dt                 AIMD 步长，单位 fs（默认: 1.0）
  -o, --output         输出 .dat 路径（默认: <文件名>_msd.dat）
  --stride             每隔 N 帧写一行（默认: 100）
  --elements H O       只导出指定元素（默认: 全部）
  --element-order      列顺序: file（文件顺序）或 alpha（字母序）

输出示例:
  #      Time(ps)      H_MSD(A2)      Ag_MSD(A2)      H_RMSD(A)      Ag_RMSD(A)
  后续可交给 plot_msd_flex.py 或 plot_line_template.py 绘图。

推荐工作流:
  python extract_msd_flex.py XDATCAR -o msd_data.dat
  python plot_msd_flex.py msd_data.dat
"""
from __future__ import annotations

import argparse
import os
import sys

from msd_common import (
    compute_msd_by_element,
    read_xdatcar,
    results_to_table,
    unique_elements,
    write_dat,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract per-element MSD/RMSD from VASP XDATCAR."
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
        "-o",
        "--output",
        default=None,
        help="Output .dat path (default: <xdatcar_basename>_msd.dat)",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=100,
        help="Write every Nth frame (default: 100)",
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
        help="Element ordering in output columns (default: file)",
    )
    return parser


def default_output_path(xdatcar: str) -> str:
    base = os.path.splitext(os.path.basename(xdatcar))[0]
    return f"{base}_msd.dat"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = args.output or default_output_path(args.xdatcar)

    positions, elem_map = read_xdatcar(args.xdatcar)
    elements = args.elements or unique_elements(elem_map, order=args.element_order)

    print(
        f"XDATCAR: {args.xdatcar}\n"
        f"frames: {positions.shape[0]}, atoms: {positions.shape[1]}\n"
        f"elements in file: {unique_elements(elem_map, order='file')}\n"
        f"elements exported: {elements}"
    )

    results = compute_msd_by_element(positions, args.dt, elem_map, elements=elements)
    data = results_to_table(results)
    write_dat(data, output, stride=args.stride, element_order=elements)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
