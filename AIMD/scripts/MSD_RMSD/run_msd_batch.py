#!/usr/bin/env python3
"""
run_msd_batch.py — 批量 MSD：扫描 $AIMD_WORK_ROOT/*/AIMD/XDATCAR

默认: 各体系写 <A>/msd_data.dat → mv → MSD_data_for_origin/<A>_msd_data.dat
默认不出图；--with-plot 时 png → MSD_png/<A>_msd_rmsd.png
dt 默认来自各体系 AIMD/INCAR 的 POTIM。
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
    ensure_result_dirs,
    iter_aimd_xdatcars,
    published_dat_path,
    published_png_path,
    system_dir_from_xdatcar,
)
from extract_msd_flex import extract_one


def plot_system(work_root: Path, xdat: Path, keep_local: bool) -> bool:
    """从已发布的 DAT 绘图；返回绘图入口是否成功。"""
    from plot_msd_flex import main as plot_main

    argv = [
        "--work-root",
        str(work_root),
        "--system-dir",
        str(system_dir_from_xdatcar(xdat)),
    ]
    if keep_local:
        argv.append("--keep-local")
    return plot_main(argv) == 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch MSD extract under AIMD_WORK_ROOT/*/AIMD/XDATCAR."
    )
    add_work_root_argument(parser)
    parser.add_argument("--dt", type=float, default=None, help="Override POTIM for all")
    parser.add_argument("--stride", type=int, default=100)
    parser.add_argument("--elements", nargs="*", default=None)
    parser.add_argument(
        "--element-order", choices=("file", "alpha"), default="file"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip if MSD_data_for_origin/<A>_msd_data.dat exists",
    )
    parser.add_argument("--keep-local", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--with-plot",
        action="store_true",
        help="Also plot and publish png (default: no plot)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    work_root = work_root_from_args(args)
    print(f"Work root: {work_root}")
    ensure_result_dirs(work_root)

    files = iter_aimd_xdatcars(work_root)
    if not files:
        print(f"No */AIMD/XDATCAR under {work_root}")
        return 1

    ok = 0
    for xdat in files:
        system_a = system_dir_from_xdatcar(xdat).name
        print("---------------------------")
        if args.skip_existing and published_dat_path(work_root, system_a).is_file():
            print(f"SKIP extract: {system_a} (archive dat exists)")
            if (
                args.with_plot
                and not args.dry_run
                and not published_png_path(work_root, system_a).is_file()
            ):
                if not plot_system(work_root, xdat, args.keep_local):
                    print(f"ERROR: plot failed for {system_a}")
                    continue
            ok += 1
            continue

        if extract_one(
            xdat,
            work_root,
            args.dt,
            None,
            args.stride,
            args.elements,
            args.element_order,
            args.keep_local,
            False,
            args.dry_run,
        ):
            ok += 1
            if args.with_plot and not args.dry_run:
                plot_system(work_root, xdat, args.keep_local)

    print("---------------------------")
    print(f"Finished: {ok}/{len(files)} systems")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
