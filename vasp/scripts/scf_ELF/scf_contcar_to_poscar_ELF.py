#!/usr/bin/env python3
"""
scf_contcar_to_poscar_ELF.py — 从 opt 的 CONTCAR 复制到 scf_ELF 并改名为 POSCAR

工作流:
  <work_root>/<A>/<B>/opt/CONTCAR  →  <work_root>/<A>/<B>/scf_ELF/POSCAR

基本用法:
  python scf_contcar_to_poscar_ELF.py --scan --work-root /path/to/calc
  python scf_contcar_to_poscar_ELF.py --system-dir /path/to/calc/Ag/50
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from bootstrap import init_imports

init_imports()

from path_config import add_work_root_argument, work_root_from_args
from scf_common import SCF_SUBDIR, setup_scf_scripts
from vasp_common import OPT_SUBDIR, iter_opt_input_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy CONTCAR from opt → scf_ELF, rename to POSCAR for SCF+ELF."
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Batch mode: scan work root for all CONTCAR → copy to sibling scf_ELF",
    )
    add_work_root_argument(parser)
    parser.add_argument(
        "--contcar",
        help="Direct path to a single CONTCAR (use with --output)",
    )
    parser.add_argument(
        "--output",
        help="Target POSCAR path (use with --contcar)",
    )
    parser.add_argument(
        "--system-dir",
        help="Single system base dir, e.g. /calc/Ag/50",
    )
    parser.add_argument(
        "--opt-dir",
        dest="system_dir",
        help="Deprecated alias for --system-dir",
    )
    parser.add_argument(
        "--write-pbs",
        action="store_true",
        help="Also write scf ELF.pbs (LELF=TRUE) in scf_ELF/ if not present",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without executing",
    )
    return parser


def copy_contcar_to_poscar(
    contcar: Path,
    poscar: Path,
    write_pbs: bool = False,
    dry_run: bool = False,
) -> bool:
    contcar = Path(contcar)
    poscar = Path(poscar)

    if not contcar.is_file():
        print(f"  ERROR: CONTCAR not found: {contcar}")
        return False

    if dry_run:
        print(f"  [dry-run] cp {contcar}")
        print(f"  [dry-run]   → {poscar}")
        if write_pbs:
            print(f"  [dry-run] write {poscar.parent}/ELF.pbs (LELF=TRUE)")
        return True

    poscar.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(contcar, poscar)
    print(f"  CONTCAR → {poscar}")

    if write_pbs:
        setup_scf_scripts(poscar.parent.parent)
        print(f"  ELF.pbs written in {poscar.parent}/ (LELF=TRUE)")

    return True


def process_single_system(
    base_dir: Path,
    write_pbs: bool = False,
    dry_run: bool = False,
) -> bool:
    contcar = base_dir / OPT_SUBDIR / "CONTCAR"
    poscar = base_dir / SCF_SUBDIR / "POSCAR"

    print(f"Processing: {base_dir}")
    print(f"  from: {contcar}")
    print(f"  to:   {poscar}")

    return copy_contcar_to_poscar(contcar, poscar, write_pbs=write_pbs, dry_run=dry_run)


def batch_scan(
    work_root: Path,
    write_pbs: bool = False,
    dry_run: bool = False,
) -> int:
    work_root = Path(work_root)

    contcar_files = iter_opt_input_files(work_root, "CONTCAR")
    if not contcar_files:
        print(f"No {OPT_SUBDIR}/CONTCAR found under {work_root}")
        return 1

    ok = 0
    for contcar in contcar_files:
        try:
            rel = contcar.relative_to(work_root)
        except ValueError:
            rel = contcar

        base_dir = work_root / rel.parent.parent
        poscar = base_dir / SCF_SUBDIR / "POSCAR"

        print("---------------------------")
        print(f"System: {base_dir.relative_to(work_root)}")
        print(f"  CONTCAR: {contcar}")

        if copy_contcar_to_poscar(contcar, poscar, write_pbs=write_pbs, dry_run=dry_run):
            ok += 1

    print("---------------------------")
    print(f"Finished: {ok}/{len(contcar_files)} systems processed.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.scan:
        work_root = work_root_from_args(args)
        print(f"Work root: {work_root}")
        return batch_scan(work_root, write_pbs=args.write_pbs, dry_run=args.dry_run)

    if args.contcar and args.output:
        poscar = Path(args.output)
        if poscar.name != "POSCAR":
            poscar = poscar.parent / "POSCAR"
        ok = copy_contcar_to_poscar(
            Path(args.contcar), poscar,
            write_pbs=args.write_pbs,
            dry_run=args.dry_run,
        )
        return 0 if ok else 1

    if args.system_dir:
        ok = process_single_system(
            Path(args.system_dir),
            write_pbs=args.write_pbs,
            dry_run=args.dry_run,
        )
        return 0 if ok else 1

    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
