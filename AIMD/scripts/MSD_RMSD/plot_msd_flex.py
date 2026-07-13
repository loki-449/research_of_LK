#!/usr/bin/env python3
"""
plot_msd_flex.py — MSD/RMSD 专用绘图（元素自动识别）

默认从 $WR/MSD_data_for_origin/<A>_msd_data.dat 读入，
图写临时文件后 mv 到 $WR/MSD_png/<A>_msd_rmsd.png。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from bootstrap import init_imports

init_imports()

from path_config import add_work_root_argument, work_root_from_args
from msd_common import (
    MSD_SUFFIX,
    RMSD_SUFFIX,
    load_dat,
    parse_elements_from_columns,
    publish_png,
    resolve_dat_for_plot,
)
from plot_line_template import do_plot


def build_msd_panels(datafile: str | Path):
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
        default=None,
        help="Input .dat (default: resolve via --system-dir / archive)",
    )
    parser.add_argument("-o", "--output", default=None, help="Temp png path before mv")
    parser.add_argument(
        "--system-dir",
        help="体系目录 $WR/<A>，用于定位汇总/本地 .dat 与 png 名",
    )
    add_work_root_argument(parser)
    parser.add_argument(
        "--keep-local",
        action="store_true",
        help="Copy png to archive but keep local file",
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        help="Do not mv png to MSD_png/",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    system_a = None
    work_root = None
    if args.system_dir:
        system_dir = Path(args.system_dir)
        system_a = system_dir.name
        work_root = work_root_from_args(args) if args.work_root else system_dir.parent
    elif args.work_root and args.datafile is None:
        print("ERROR: with --work-root alone, also pass datafile or --system-dir")
        return 1
    else:
        work_root = work_root_from_args(args) if args.work_root else None

    try:
        datafile = resolve_dat_for_plot(work_root, system_a, args.datafile)
    except FileNotFoundError as exc:
        if args.datafile:
            datafile = Path(args.datafile)
            if not datafile.is_file():
                print(f"ERROR: {exc}")
                return 1
        else:
            print(f"ERROR: {exc}")
            return 1

    if system_a is None and work_root and datafile.name.endswith("_msd_data.dat"):
        system_a = datafile.name[: -len("_msd_data.dat")]

    tmp_png = Path(args.output) if args.output else Path(f"{datafile.stem}_msd_rmsd.png")
    if system_a and work_root and not args.output:
        tmp_png = (work_root / system_a) / f"{system_a}_tmp_msd_rmsd.png"

    panels = build_msd_panels(datafile)
    print(f"datafile: {datafile}")
    print(
        "elements:",
        [col.replace(MSD_SUFFIX, "") for col in panels[0]["y_columns"]],
    )

    do_plot(datafile=str(datafile), output=str(tmp_png), panels=panels)

    if not args.no_publish and system_a and work_root:
        publish_png(tmp_png, work_root, system_a, keep_local=args.keep_local)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
