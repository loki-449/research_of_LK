#!/usr/bin/env python3
"""
make_potcar.py — 按元素顺序拼接 VASP POTCAR（opt_ELF 用）

用途:
  从赝势库选取最优单元素 POTCAR，拼接后写入 opt_ELF 目录。
  POTCAR 仅放置在 opt_ELF/ 中。

择优规则:
  1. ZVAL（价电子数）最大者优先
  2. ZVAL 相同时，取第一行日期最新者

基本用法:
  python make_potcar.py --scan ./vasp/opt
  python make_potcar.py --poscar vasp/opt/Ag/50/opt_ELF/POSCAR -o vasp/opt/Ag/50/opt_ELF/POTCAR

默认赝势库:
  /home/test1/hhy/basic/psudopotential/PAW-GGA-PBE
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from vasp_common import (
    DEFAULT_PBE_LIB,
    OPT_SUBDIR,
    assemble_potcar,
    read_poscar_elements,
    setup_opt_scripts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble VASP POTCAR from PBE pseudopotential library (opt_ELF only)."
    )
    parser.add_argument(
        "elements",
        nargs="*",
        help="Element symbols in order (optional if --poscar is given)",
    )
    parser.add_argument(
        "--poscar",
        help="Read element order from POSCAR",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="POTCAR",
        help="Output POTCAR path (default: POTCAR)",
    )
    parser.add_argument(
        "--pbe-lib",
        default=os.environ.get("PBE_LIB", DEFAULT_PBE_LIB),
        help=f"PBE pseudopotential library root (default: {DEFAULT_PBE_LIB})",
    )
    parser.add_argument(
        "--keep-single",
        action="store_true",
        help="Keep per-element <Elem>.POTCAR files in output directory",
    )
    parser.add_argument(
        "--scan",
        metavar="ELF_ROOT",
        help="Batch mode: process opt_ELF under the root",
    )
    return parser


def resolve_elements(args) -> List[str]:
    if args.poscar:
        return read_poscar_elements(args.poscar)
    if args.elements:
        return args.elements
    raise ValueError("Specify elements or use --poscar")


def opt_potcar_path(base_dir: Path) -> Path:
    """Return POTCAR output path under opt_ELF only."""
    return Path(base_dir) / OPT_SUBDIR / "POTCAR"


def make_one(
    elements: List[str],
    output: Path,
    pbe_lib: str,
    keep_single: bool = False,
    write_pbs: bool = True,
) -> None:
    sources = assemble_potcar(
        elements,
        output,
        pbe_lib=pbe_lib,
        keep_single=keep_single,
    )
    if write_pbs:
        base = output.parent.parent if output.parent.name == OPT_SUBDIR else output.parent
        setup_opt_scripts(base)

    print(f"POTCAR written: {output}")
    print(f"  rule: max ZVAL, then newest date on line 1")
    for elem, info in sources.items():
        print(f"  {elem} -> {info['dir']} (ZVAL={info['zval']}, {info['date']})")


def make_for_base(
    elements: List[str],
    base_dir: Path,
    pbe_lib: str,
    keep_single: bool,
) -> None:
    """Write POTCAR to opt_ELF only."""
    output = opt_potcar_path(base_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    sources = assemble_potcar(elements, output, pbe_lib=pbe_lib, keep_single=keep_single)
    print(f"POTCAR -> {base_dir}/{OPT_SUBDIR}/POTCAR")
    for elem, info in sources.items():
        print(f"  {elem} -> {info['dir']} (ZVAL={info['zval']}, {info['date']})")


def batch_scan(elf_root: Path, pbe_lib: str, keep_single: bool) -> int:
    poscars = sorted(elf_root.rglob(f"{OPT_SUBDIR}/POSCAR"))
    if not poscars:
        print(f"No {OPT_SUBDIR}/POSCAR found under {elf_root}")
        return 1

    bases = sorted({p.parent.parent for p in poscars})
    ok = 0
    for base_dir in bases:
        opt_poscar = base_dir / OPT_SUBDIR / "POSCAR"
        print(f"Processing: {base_dir}")
        try:
            elements = read_poscar_elements(opt_poscar)
            make_for_base(elements, base_dir, pbe_lib, keep_single=keep_single)
            ok += 1
        except (ValueError, FileNotFoundError, OSError) as exc:
            print(f"  ERROR: {exc}")
        print("---------------------------")

    print(f"Finished: {ok}/{len(bases)} systems processed.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.scan:
        return batch_scan(Path(args.scan), args.pbe_lib, args.keep_single)

    try:
        elements = resolve_elements(args)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        build_parser().print_help()
        return 1

    output = Path(args.output)
    # If output path is in opt_ELF, use make_for_base
    if output.parent.name == OPT_SUBDIR:
        make_for_base(elements, output.parent.parent, args.pbe_lib, args.keep_single)
    else:
        make_one(elements, output, args.pbe_lib, keep_single=args.keep_single)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
