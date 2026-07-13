#!/usr/bin/env python3
"""
setup_elf_workflow.py — ELF 工作目录建立（从 QE 计算文件夹扫描并生成 opt_ELF 结构）

用途:
  扫描 QE 计算目录下符合命名规则的子文件夹（默认 *GPa*），解析材料名 / 压强 / 温度，
  在 vasp/opt 根目录下建立体系层级目录:
    vasp/opt/<A>/<B>/opt_ELF/  — 结构优化 (Relaxation INCAR)

  scf_ELF 目录由 vasp/scf_ELF/ 下脚本独立管理。

依赖:
  无第三方依赖（仅标准库）

基本用法:
  # 仅建立目录 + ELF.pbs
  python setup_elf_workflow.py /path/to/QE_folder

  # 建立目录 + ELF.pbs + POSCAR
  python setup_elf_workflow.py /path/to/QE_folder --with-poscar

常用参数:
  qe_dir               QE 计算根目录（必填）
  --elf-root           体系输出根目录（默认: ./vasp/opt）
  --pattern            子目录匹配模式（默认: *GPa*）
  --with-poscar        批量生成 POSCAR 到 opt_ELF
  --dry-run            只打印计划，不实际创建
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 确保可导入同目录下 vasp_common
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from vasp_common import (
    OPT_SUBDIR,
    find_qe_system_dirs,
    find_relax_in,
    parse_qe_system,
    setup_opt_scripts,
)
from make_poscar import make_poscar_for_base


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create opt_ELF workflow directories and PBS scripts from QE folders."
    )
    parser.add_argument("qe_dir", help="QE calculation root directory")
    parser.add_argument(
        "--elf-root",
        default="./vasp/opt",
        help="Output root directory (default: ./vasp/opt)",
    )
    parser.add_argument(
        "--pattern",
        default="*GPa*",
        help="Glob pattern for QE system subdirectories (default: *GPa*)",
    )
    parser.add_argument(
        "--with-poscar",
        action="store_true",
        help="Also generate POSCAR into opt_ELF (batch)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without creating files",
    )
    return parser


def setup_one_system(
    system_dir: Path,
    elf_root: Path,
    with_poscar: bool = False,
    dry_run: bool = False,
) -> bool:
    info = parse_qe_system(system_dir)
    if info is None:
        print(f"  SKIP: name parse failed ({system_dir.name})")
        return False

    relax_in = find_relax_in(system_dir)
    if relax_in is None:
        print(f"  SKIP: relax.in not found in {system_dir}")
        return False

    target_dir = elf_root / info.material / info.pressure
    print(f"Processing: {info.basename}")
    print(f"  material={info.material}  pressure={info.pressure}  temperature={info.temperature}K")
    print(f"  relax.in: {relax_in}")
    print(f"  target:   {target_dir}/{OPT_SUBDIR}")

    if dry_run:
        msg = f"  [dry-run] would create {OPT_SUBDIR}/ELF.pbs"
        if with_poscar:
            msg += " + POSCAR"
        print(msg)
        return True

    opt_dir = setup_opt_scripts(target_dir)
    print(f"  {opt_dir.name}/ELF.pbs written (Relaxation INCAR)")

    if with_poscar:
        make_poscar_for_base(relax_in, target_dir, write_pbs=False)
        print(f"  POSCAR written -> {OPT_SUBDIR}/")

    print(f"  DONE: {target_dir}")
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
        try:
            if setup_one_system(
                system_dir,
                elf_root,
                with_poscar=args.with_poscar,
                dry_run=args.dry_run,
            ):
                ok += 1
        except (ValueError, OSError) as exc:
            print(f"  ERROR: {exc}")
        print("---------------------------")

    print(f"Finished: {ok}/{len(systems)} systems processed.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit