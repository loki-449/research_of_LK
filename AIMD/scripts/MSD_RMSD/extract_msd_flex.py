#!/usr/bin/env python3
"""
extract_msd_flex.py — 从 XDATCAR 提取 MSD/RMSD（元素自动识别）

用途:
  读取 VASP XDATCAR → 写 $WR/<A>/msd_data.dat → 默认 mv 到
  $WR/MSD_data_for_origin/<A>_msd_data.dat

dt:
  未给 --dt 时从同体系 AIMD/INCAR 的 POTIM 读取（fs）。
  Time(ps) = frame_index * POTIM / 1000。

基本用法:
  python extract_msd_flex.py $AIMD_WORK_ROOT/Ba3AgH7/AIMD/XDATCAR
  python extract_msd_flex.py --scan --work-root $AIMD_WORK_ROOT
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from bootstrap import init_imports

init_imports()

from path_config import add_work_root_argument, resolve_work_root, work_root_from_args
from msd_common import (
    aimd_dir_of,
    compute_msd_by_element,
    ensure_result_dirs,
    iter_aimd_xdatcars,
    local_dat_path,
    publish_dat,
    read_xdatcar,
    resolve_dt,
    results_to_table,
    system_dir_from_xdatcar,
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
        default=None,
        help="Path to XDATCAR (omit when using --scan)",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=None,
        help="AIMD timestep in fs (default: read POTIM from AIMD/INCAR)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Local .dat path before mv (default: <A>/msd_data.dat)",
    )
    parser.add_argument("--stride", type=int, default=100, help="Write every Nth frame")
    parser.add_argument(
        "--elements",
        nargs="*",
        default=None,
        help="Only include selected elements (default: all)",
    )
    parser.add_argument(
        "--element-order",
        choices=("file", "alpha"),
        default="file",
        help="Element column order (default: file)",
    )
    add_work_root_argument(parser)
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Batch: scan $AIMD_WORK_ROOT/*/AIMD/XDATCAR",
    )
    parser.add_argument(
        "--keep-local",
        action="store_true",
        help="Copy to archive dirs but keep <A>/msd_data.dat",
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        help="Do not mv/copy to MSD_data_for_origin/",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan only")
    return parser


def extract_one(
    xdatcar: Path,
    work_root: Path | None,
    dt: float | None,
    output: Path | None,
    stride: int,
    elements: list[str] | None,
    element_order: str,
    keep_local: bool,
    no_publish: bool,
    dry_run: bool,
) -> bool:
    system_dir = system_dir_from_xdatcar(xdatcar)
    system_a = system_dir.name
    aimd_dir = aimd_dir_of(system_dir)
    wr = work_root or system_dir.parent

    try:
        timestep, dt_src = resolve_dt(aimd_dir, cli_dt=dt)
    except FileNotFoundError as exc:
        print(f"  ERROR: {exc}")
        return False

    local_out = output or local_dat_path(system_dir)

    print(f"Processing: {system_a}")
    print(f"  XDATCAR: {xdatcar}")
    print(f"  dt: {timestep} fs ({dt_src})")
    print(f"  local:   {local_out}")

    if dry_run:
        print(f"  [dry-run] would write + publish under {wr}")
        return True

    positions, elem_map = read_xdatcar(xdatcar)
    elems = elements or unique_elements(elem_map, order=element_order)
    print(
        f"  frames: {positions.shape[0]}, atoms: {positions.shape[1]}, "
        f"elements: {elems}"
    )

    results = compute_msd_by_element(
        positions, timestep, elem_map, elements=elems
    )
    data = results_to_table(results)
    write_dat(data, local_out, stride=stride, element_order=elems)

    if not no_publish:
        ensure_result_dirs(wr)
        publish_dat(local_out, wr, system_a, keep_local=keep_local)
    return True


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.scan:
        work_root = work_root_from_args(args)
        print(f"Work root: {work_root}")
        files = iter_aimd_xdatcars(work_root)
        if not files:
            print(f"No */AIMD/XDATCAR under {work_root}")
            return 1
        ok = 0
        for xdat in files:
            print("---------------------------")
            if extract_one(
                xdat,
                work_root,
                args.dt,
                None,
                args.stride,
                args.elements,
                args.element_order,
                args.keep_local,
                args.no_publish,
                args.dry_run,
            ):
                ok += 1
        print("---------------------------")
        print(f"Finished: {ok}/{len(files)}")
        return 0 if ok else 1

    if not args.xdatcar:
        build_parser().print_help()
        return 1

    xdat = Path(args.xdatcar)
    wr = resolve_work_root(args.work_root) if args.work_root else system_dir_from_xdatcar(xdat).parent
    out = Path(args.output) if args.output else None
    ok = extract_one(
        xdat,
        wr,
        args.dt,
        out,
        args.stride,
        args.elements,
        args.element_order,
        args.keep_local,
        args.no_publish,
        args.dry_run,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
