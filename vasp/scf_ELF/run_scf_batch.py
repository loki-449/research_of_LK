#!/usr/bin/env python3
"""
run_scf_batch.py — SCF + ELF 计算批量部署

用途:
  从 QE 计算文件夹批量建立 scf_ELF 目录，依次执行:
    1. 建立 vasp/scf_ELF/<A>/<B>/scf_ELF
    2. 写入 ELF.pbs（LELF=TRUE INCAR）
    3. 从 relax.in 生成 POSCAR
    4. 按元素顺序拼接 POTCAR

  opt_ELF 部分由 vasp/opt/run_elf_batch.py 独立管理。

目录结构:
  vasp/scf_ELF/<A>/<B>/scf_ELF/   ELF 计算 (LELF=TRUE)

依赖:
  scf_common.py（间接依赖 vasp/opt/vasp_common.py）

基本用法:
  python run_scf_batch.py /path/to/QE_folder
  python run_scf_batch.py /path/to/QE_folder --elf-root ./vasp/scf_ELF --pbe-lib /path/to/PAW-GGA-PBE
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from scf_common import (
    SCF_SUBDIR,
    deploy_scf_system,
)

# 从 vasp/opt/vasp_common 导入共享工具
_OPT_DIR = _SCRIPT_DIR.parent / "opt"
if str(_OPT_DIR) not in sys.path:
    sys.path.insert(0, str(_OPT_DIR))

from vasp_common import (  # noqa: E402
    DEFAULT_PBE_LIB,
    find_qe_system_dirs,
    find_relax_in,
    parse_qe_system,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch deploy scf_ELF calculations from QE folders."
    )
    parser.add_argument("qe_dir", help="QE calculation root directory")
    parser.add_argument(
        "--elf-root",
        default="./vasp/scf_ELF",
        help="Output root for scf_ELF (default: ./vasp/scf_ELF)",
    )
    parser.add_argument(
        "--pbe-lib",
        default=os.environ.get("PBE_LIB", DEFAULT_PBE_LIB),
        help="PBE pseudopotential library root",
    )
    parser.add_argument("--pattern", default="*GPa*", help="System folder pattern")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip if POSCAR and POTCAR already exist in scf_ELF",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan only, no writes")
    return parser


def inputs_complete(base_dir: Path) -> bool:
    d = base_dir / SCF_SUBDIR
    return (d / "POSCAR").is_file() and (d / "POTCAR").is_file()


def process_one(
    system_dir: Path,
    elf_root: Path,
    pbe_lib: str,
    skip_existing: bool,
    dry_run: bool,
) -> bool:
    info = parse_qe_system(system_dir)
    if info is None:
        print(f"  SKIP: name parse failed ({system_dir.name})")
        return False

    relax_in = find_relax_in(system_dir)
    if relax_in is None:
        print(f"  SKIP: relax.in not found")
        return False

    base_dir = elf_root / info.material / info.pressure

    print(f"Processing: {info.basename}")
    print(f"  A={info.material}  B={info.pressure}  C={info.temperature}K")
    print(f"  relax.in: {relax_in}")
    print(f"  target:   {base_dir}/{SCF_SUBDIR}")

    if skip_existing and inputs_complete(base_dir):
        print(f"  SKIP: inputs already exist in {SCF_SUBDIR}")
        return True

    if dry_run:
        print(f"  [dry-run] would create {SCF_SUBDIR} with PBS/POSCAR/POTCAR")
        return True

    try:
        structure, sources = deploy_scf_system(relax_in, base_dir, pbe_lib=pbe_lib)
        print(f"  {SCF_SUBDIR}/ELF.pbs written (ELF INCAR, LELF=TRUE)")
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"  ERROR: {exc}")
        if (base_dir / SCF_SUBDIR / "POSCAR").is_file():
            print(f"  DONE (partial): {base_dir}")
        return False

    elem_summary = " ".join(
        f"{e}({c})" for e, c in zip(structure.elements, structure.counts)
    )
    print(f"  POSCAR: {elem_summary} -> {SCF_SUBDIR}/")
    for elem, meta in sources.items():
        print(f"  {elem} -> {meta['dir']} (ZVAL={meta['zval']}, {meta['date']})")
    print(f"  POTCAR assembled -> {SCF_SUBDIR}/")
    print(f"  DONE: {base_dir}")
    return True


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    qe_dir = Path(args.qe_dir)
    elf_root = Path(args.elf_root)

    systems = find_qe_system_dirs(qe_dir, pattern=args.pattern)
    if not systems:
        print(f"No system directories matched '{args.pattern}' under {qe_dir}")
        return 1

    ok = 0
    for system_dir in systems:
        print("---------------------------")
        if process_one(
            system_dir,
            elf_root,
            args.pbe_lib,
            skip_existing=args.skip_existing,
            dry_run=args.dry_run,
        ):
            ok += 1

    print("---------------------------")
    print(f"All done. {ok}/{len(systems)} systems processed.")
    return 0 if ok else 1


if __name__ ==