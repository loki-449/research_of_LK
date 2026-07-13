#!/usr/bin/env python3
"""
scf_contcar_to_poscar_ELF.py — 从 opt_ELF 的 CONTCAR 复制到 scf_ELF 并改名为 POSCAR

用途:
  opt 结构优化完成后，CONTCAR 是优化后的结构。本脚本:
    1. 扫描 vasp/opt/<A>/<B>/opt_ELF/CONTCAR
    2. 复制到 vasp/scf_ELF/<A>/<B>/scf_ELF/ 并改名为 POSCAR
    3. 若 scf_ELF/ 目录不存在则自动创建
    4. 可选同时写入 scf ELF.pbs（LELF=TRUE INCAR）

工作流:
  vasp/opt/<A>/<B>/opt_ELF/CONTCAR
    ──cp──>
  vasp/scf_ELF/<A>/<B>/scf_ELF/POSCAR

基本用法:
  # 批量扫描 opt 下的 CONTCAR 并复制到 scf_ELF
  python scf_contcar_to_poscar_ELF.py --scan

  # 指定单个体系
  python scf_contcar_to_poscar_ELF.py \\
      --opt-dir vasp/opt/Ag/50 \\
      --scf-dir vasp/scf_ELF/Ag/50

  # 直接指定 CONTCAR 路径 + 输出 POSCAR 路径
  python scf_contcar_to_poscar_ELF.py \\
      --contcar vasp/opt/Ag/50/opt_ELF/CONTCAR \\
      --output vasp/scf_ELF/Ag/50/scf_ELF/POSCAR

  # 同时写入 ELF.pbs
  python scf_contcar_to_poscar_ELF.py --scan --write-pbs
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from scf_common import SCF_SUBDIR, setup_scf_scripts

# ============================================================
# 默认路径
# ============================================================
OPT_ROOT_DEFAULT = "./vasp/opt"
SCF_ROOT_DEFAULT = "./vasp/scf_ELF"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy CONTCAR from opt_ELF → scf_ELF, rename to POSCAR for SCF+ELF."
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Batch mode: scan opt root for all CONTCAR → copy to matching scf_ELF paths",
    )
    parser.add_argument(
        "--opt-root",
        default=OPT_ROOT_DEFAULT,
        help=f"opt root directory (default: {OPT_ROOT_DEFAULT})",
    )
    parser.add_argument(
        "--scf-root",
        default=SCF_ROOT_DEFAULT,
        help=f"scf_ELF root directory (default: {SCF_ROOT_DEFAULT})",
    )
    parser.add_argument(
        "--contcar",
        help="Direct path to a single CONTCAR (use with --output)",
    )
    parser.add_argument(
        "--output",
        help="Target POSCAR path (use with --contcar)",
    )
    parser.add_argument(
        "--opt-dir",
        help="Single opt base dir, e.g. vasp/opt/Ag/50 (use with --scf-dir)",
    )
    parser.add_argument(
        "--scf-dir",
        help="Single scf base dir, e.g. vasp/scf_ELF/Ag/50 (use with --opt-dir)",
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
    """Copy CONTCAR → POSCAR. Optionally write scf ELF.pbs."""
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
        # poscar.parent = scf_ELF/, poscar.parent.parent = base_dir
        setup_scf_scripts(poscar.parent.parent)
        print(f"  ELF.pbs written in {poscar.parent}/ (LELF=TRUE)")

    return True


def process_single_system(
    opt_base: Path,
    scf_base: Path,
    write_pbs: bool = False,
    dry_run: bool = False,
) -> bool:
    """Single system: vasp/opt/<A>/<B>/opt_ELF/CONTCAR → vasp/scf_ELF/<A>/<B>/scf_ELF/POSCAR."""
    contcar = opt_base / "opt_ELF" / "CONTCAR"
    poscar = scf_base / "scf_ELF" / "POSCAR"

    print(f"Processing: {scf_base.relative_to(scf_base.parents[1]) if len(scf_base.parents) >= 2 else scf_base}")
    print(f"  from: {contcar}")
    print(f"  to:   {poscar}")

    return copy_contcar_to_poscar(contcar, poscar, write_pbs=write_pbs, dry_run=dry_run)


def batch_scan(
    opt_root: Path,
    scf_root: Path,
    write_pbs: bool = False,
    dry_run: bool = False,
) -> int:
    """Scan opt_root/**/opt_ELF/CONTCAR, copy each to matching scf_root path."""
    opt_root = Path(opt_root)
    scf_root = Path(scf_root)

    contcar_files = sorted(opt_root.rglob("opt_ELF/CONTCAR"))
    if not contcar_files:
        print(f"No opt_ELF/CONTCAR found under {opt_root}")
        return 1

    ok = 0
    for contcar in contcar_files:
        try:
            rel = contcar.relative_to(opt_root)  # e.g. Ag/50/opt_ELF/CONTCAR
        except ValueError:
            rel = contcar

        system_rel = rel.parent.parent  # Ag/50/
        scf_base = scf_root / system_rel
        poscar = scf_base / SCF_SUBDIR / "POSCAR"

        print("---------------------------")
        print(f"System: {system_rel}")
        print(f"  CONTCAR: {contcar}")

        if copy_contcar_to_poscar(contcar, poscar, write_pbs=write_pbs, dry_run=dry_run):
            ok += 1

    print("---------------------------")
    print(f"Finished: {ok}/{len(contcar_files)} systems processed.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # --scan: batch mode
    if args.scan:
        return batch_scan(
            Path(args.opt_root),
            Path(args.scf_root),
            write_pbs=args.write_pbs,
            dry_run=args.dry_run,
        )

    # --contcar + --output: direct mode
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

    # --opt-dir + --scf-dir: single system mode
    if args.opt_dir and args.scf_dir:
        ok = process_single_system(
            Path(args.opt_dir),
            Path(args.scf_dir),
            write_pbs=args.write_pbs,
            dry_run=args.dry_run,
        )
        return 0 if ok else 1

    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
