#!/usr/bin/env python3
"""
plot_msd_flex.py — MSD/RMSD 专用绘图（元素自动识别）

用途:
  读取 extract_msd_flex.py 输出的 .dat 文件，自动识别元素列并绘制 MSD/RMSD 双子图。
  无需在脚本中写死元素名（如 H/Ag/Ba），换体系直接换数据文件即可。

依赖:
  pip install numpy matplotlib

基本用法:
  python plot_msd_flex.py
  python plot_msd_flex.py msd_data.dat
  python plot_msd_flex.py path/to/data.dat -o output.png

常用参数:
  datafile             输入 .dat 路径（默认: msd_data.dat）
  -o, --output         输出图片路径（默认: <数据文件名>_msd_rmsd.png）

推荐工作流:
  python extract_msd_flex.py XDATCAR -o msd_data.dat
  python plot_msd_flex.py msd_data.dat

自定义样式:
  修改同目录下 plot_line_template.py 顶部的 LINE_STYLE / DEFAULT_COLORS 等配置，
  本脚本会自动继承这些样式设置。
"""
from __future__ import annotations

import argparse
import os
import sys

from msd_common import MSD_SUFFIX, RMSD_SUFFIX, load_dat, parse_elements_from_columns
from plot_line_template import do_plot

DEFAULT_DATAFILE = "msd_data.dat"
DEFAULT_OUTPUT = "msd_rmsd.png"


def build_msd_panels(datafile: str):
    data = load_dat(datafile)
    elems = parse_elements_from_columns(list(data.keys()), suffix=MSD_SUFFIX)
    if not elems:
        raise ValueError(
            f"No MSD columns found in {datafile}. "
            f"Expected columns like '<Element>{MSD_SUFFIX}'."
        )

    return [
        {
            "title": "MSD",
            "x_col": "Time(ps)",
            "y_columns": [f"{elem}{MSD_SUFFIX}" for elem in elems],
            "ylabel": "MSD (A^2)",
        },
        {
            "title": "RMSD",
            "x_col": "Time(ps)",
            "y_columns": [f"{elem}{RMSD_SUFFIX}" for elem in elems],
            "ylabel": "RMSD (A)",
        },
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot MSD/RMSD curves with auto element detection."
    )
    parser.add_argument(
        "datafile",
        nargs="?",
        default=DEFAULT_DATAFILE,
        help=f"Input .dat file (default: {DEFAULT_DATAFILE})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output image path (default: <datafile_basename>_msd_rmsd.png)",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    base = os.path.splitext(os.path.basename(args.datafile))[0]
    output = args.output or f"{base}_msd_rmsd.png"
    panels = build_msd_panels(args.datafile)

    print(f"datafile: {args.datafile}")
    print(
        "elements:",
        [col.replace(MSD_SUFFIX, "") for col in panels[0]["y_columns"]],
    )

    do_plot(datafile=args.datafile, output=output, panels=panels)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
