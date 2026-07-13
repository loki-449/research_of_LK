#!/usr/bin/env python3
"""
setup_opt_workflow.py — opt 工作目录建立（从 QE 计算文件夹扫描并生成 opt 结构）

用途:
  扫描 QE 计算目录下符合命名规则的子文件夹（默认 *GPa*），解析材料名 / 压强 / 温度，
  在计算工作根目录下建立体系层级:
    <work_root>/<A>/<B>/opt/  — 结构优化 (Relaxation INCAR)

  脚本可安装于任意路径；工作目录通过 --work-root 或环境变量 VASP_WORK_ROOT 指定。

基本用法:
  python setup_opt_workflow.py /path/to/QE_folder --work-root /path/to/calc
  export VASP_WORK_ROOT=/path/to/calc
  python /installed/vasp/scripts/opt/setup_opt_workflow.py /path/to/QE_folder
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from bootstrap import init_imports

init_imports()

from path_config import add_work_root_argument, work_root_from_args
from vasp_common import (
    OPT_PBS_SCRIPT,
    OPT_SUBDIR,
    find_qe_system_dirs,
    find_relax_in,
    parse_qe_system,
    setup_opt_scripts,
)
from make_poscar import make_poscar_for_base


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create opt workflow directories and PBS scripts from QE folders."
    )
    parser.add_argument("qe_dir", help="QE calculation root directory")
    add_work_root_argument(parser)
    parser.add_argument(
        "--pattern",
        default="*GPa*",
        help="Glob pattern for QE system subdirectories (default: *GPa*)",
    )
    parser.add_argument(
        "--with-poscar",
        action="store_true",
        help="Also generate POSCAR into opt (batch)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without creating files",
    )
    return parser


def setup_one_system(
    system_dir: Path,
    work_root: Path,
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

    target_dir = work_root / info.material / info.pressure
    print(f"Processing: {info.basename}")
    print(f"  material={info.material}  pressure={info.pressure}  temperature={info.temperature}K")
    print(f"  relax.in: {relax_in}")
    print(f"  target:   {target_dir}/{OPT_SUBDIR}")

    if dry_run:
        msg = f"  [dry-run] would create {OPT_SUBDIR}/{OPT_PBS_SCRIPT}"
        if with_poscar:
            msg += " + POSCAR"
        print(msg)
        return True

    opt_dir = setup_opt_scripts(target_dir)
    print(f"  {opt_dir.name}/{OPT_PBS_SCRIPT} written (Relaxation INCAR)")

    if with_poscar:
        make_poscar_for_base(relax_in, target_dir, write_pbs=False)
        print(f"  POSCAR written -> {OPT_SUBDIR}/")

    print(f"  DONE: {target_dir}")
    return True


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    qe_dir = Path(args.qe_dir)
    work_root = work_root_from_args(args)
    print(f"Work root: {work_root}")

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
                work_root,
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
    raise SystemExit(main())
