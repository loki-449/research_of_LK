#!/usr/bin/env python3
"""
make_poscar.py — 从 QE relax.in 生成 VASP POSCAR（opt_ELF 用）

用途:
  读取 QE relax.in，生成 POSCAR 并写入 opt_ELF 目录:
    vasp/opt/<A>/<B>/opt_ELF/POSCAR

默认只写 POSCAR，不覆盖已有 ELF.pbs。

基本用法:
  # 单个 QE 体系目录
  python make_poscar.py /path/to/Ag-H-50GPa-300K --elf-root ./vasp/opt

  # 直接指定 relax.in + ELF 基目录
  python make_poscar.py --relax-in /path/to/relax.in --base-dir vasp/opt/Ag/50

  # 批量：扫描 QE 根目录
  python make_poscar.py --scan /path/to/QE_folder --elf-root ./vasp/opt

  # 通过 setup_elf_workflow 一步完成目录+PBS+POSCAR
  python setup_elf_workflow.py /path/to/QE_folder --with-poscar
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from vasp_common import (
    OPT_SUBDIR,
    deploy_poscar_to_opt,
    find_qe_system_dirs,
    find_relax_in,
    parse_qe_system,
    parse_relax_in,
    setup_opt_scripts,
    system_base_dir,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VASP POSCAR from QE relax.in into opt_ELF."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="QE system directory, or relax.in file path",
    )
    parser.add_argument(
        "--relax-in",
        help="Explicit relax.in path (use with --base-dir)",
    )
    parser.add_argument(
        "--base-dir",
        help="vasp/opt base directory, e.g. vasp/opt/Ag/50 (writes to opt_ELF)",
    )
    parser.add_argument(
        "--scan",
        metavar="QE_DIR",
        help="Batch mode: scan QE root for *GPa* systems",
    )
    parser.add_argument(
        "--elf-root",
        default="./vasp/opt",
        help="Output root for batch/single mode (default: ./vasp/opt)",
    )
    parser.add_argument(
        "--pattern",
        default="*GPa*",
        help="Batch mode subdirectory glob (default: *GPa*)",
    )
    parser.add_argument(
        "--write-pbs",
        action="store_true",
        help="Also write/overwrite ELF.pbs in opt_ELF",
    )
    return parser


def resolve_relax_in(path: Path) -> Path:
    if path.is_file():
        return path
    if path.is_dir():
        relax_in = find_relax_in(path)
        if relax_in is None:
            raise FileNotFoundError(f"relax.in not found under {path}")
        return relax_in
    raise FileNotFoundError(f"Input not found: {path}")


def is_opt_base_dir(path: Path) -> bool:
    """Check if path looks like vasp/opt/<A>/<B>/ with opt_ELF subdir."""
    if not path.is_dir():
        return False
    if (path / OPT_SUBDIR).is_dir():
        return True
    return path.name == OPT_SUBDIR


def make_poscar_for_base(
    relax_in: Path,
    base_dir: Path,
    write_pbs: bool = False,
) -> bool:
    """Generate POSCAR into opt_ELF under base_dir."""
    base_dir = Path(base_dir)

    structure = parse_relax_in(relax_in)
    if write_pbs:
        setup_opt_scripts(base_dir)
    else:
        opt_dir = base_dir / OPT_SUBDIR
        if not opt_dir.is_dir():
            print(f"  WARNING: {OPT_SUBDIR} missing under {base_dir}; creating it")
            print(f"  (run setup_elf_workflow.py first if ELF.pbs is also needed)")

    deploy_poscar_to_opt(structure, base_dir)

    elem_info = " ".join(
        f"{e}({c})" for e, c in zip(structure.elements, structure.counts)
    )
    print(f"POSCAR -> {base_dir}/{OPT_SUBDIR}/POSCAR")
    if write_pbs:
        print(f"  ELF.pbs written in {OPT_SUBDIR}")
    print(f"  elements: {elem_info}")
    print(f"  source:   {relax_in}")
    return True


def process_qe_system(
    system_dir: Path,
    elf_root: Path,
    write_pbs: bool = False,
) -> bool:
    """Process one QE system folder -> vasp/opt/<A>/<B>/opt_ELF."""
    info = parse_qe_system(system_dir)
    if info is None:
        print(f"  SKIP: name parse failed ({system_dir.name})")
        return False

    relax_in = find_relax_in(system_dir)
    if relax_in is None:
        print(f"  SKIP: relax.in not found ({system_dir.name})")
        return False

    base_dir = system_base_dir(elf_root, info.material, info.pressure)
    print(f"Processing: {info.basename}")
    print(f"  material={info.material}  pressure={info.pressure}  temperature={info.temperature}K")
    print(f"  relax.in: {relax_in}")
    print(f"  target:   {base_dir}/{OPT_SUBDIR}")

    make_poscar_for_base(relax_in, base_dir, write_pbs=write_pbs)
    print(f"  DONE: {base_dir}")
    return True


def batch_scan(
    qe_dir: Path,
    elf_root: Path,
    pattern: str,
    write_pbs: bool = False,
) -> int:
    systems = find_qe_system_dirs(qe_dir, pattern=pattern)
    if not systems:
        print(f"No systems matched '{pattern}' under {qe_dir}")
        return 1

    ok = 0
    for system_dir in systems:
        print("---------------------------")
        try:
            if process_qe_system(system_dir, elf_root, write_pbs=write_pbs):
                ok += 1
        except (ValueError, OSError) as exc:
            print(f"  ERROR: {exc}")
        print("---------------------------")

    print(f"Finished: {ok}/{len(systems)} systems processed.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.scan:
        return batch_scan(
            Path(args.scan),
            Path(args.elf_root),
            args.pattern,
            write_pbs=args.write_pbs,
        )

    # --relax-in + --base-dir
    if args.relax_in and args.base_dir:
        try:
            make_poscar_for_base(
                Path(args.relax_in),
                Path(args.base_dir),
                write_pbs=args.write_pbs,
            )
            return 0
        except (ValueError, OSError, FileNotFoundError) as exc:
            print(f"ERROR: {exc}")
            return 1

    if not args.input:
        build_parser().print_help()
        return 1

    input_path = Path(args.input)

    # opt_ELF base dir + --relax-in
    if is_opt_base_dir(input_path):
        base = input_path if input_path.name != OPT_SUBDIR else input_path.parent
        relax_in = Path(args.relax_in) if args.relax_in else None
        if relax_in is None:
            print("ERROR: vasp/opt base dir given; please also specify --relax-in")
            return 1
        try:
            make_poscar_for_base(relax_in, base, write_pbs=args.write_pbs)
            return 0
        except (ValueError, OSError, FileNotFoundError) as exc:
            print(f"ERROR: {exc}")
            return 1

    # relax.in file + optional --base-dir
    if input_path.is_file() and input_path.name.endswith(".in"):
        if not args.base_dir:
            print("ERROR: relax.in given; please also specify --base-dir vasp/opt/<A>/<B>")
            return 1
        try:
            make_poscar_for_base(input_path, Path(args.base_dir), write_pbs=args.write_pbs)
            return 0
        except (ValueError, OSError, FileNotFoundError) as exc:
            print(f"ERROR: {exc}")
            return 1

    # QE system directory (single folder)
    if input_path.is_dir():
        try:
            return 0 if process_qe_system(
                input_path, Path(args.elf_root), write_pbs=args.write_pbs
            ) else 1
        except (ValueError, OSError, FileNotFoundError) as exc:
            print(f"ERROR: {exc}")
            return 1

    print(f"ERROR: cannot interpret input: {input_path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
