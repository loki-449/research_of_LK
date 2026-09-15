#!/usr/bin/env python3
"""
scf_common.py — ELF scf 计算公共模块

功能:
  - SCF + ELF 计算的 INCAR 模板与 PBS 脚本生成
  - scf_ELF 目录管理与部署

依赖 scripts/lib/vasp_common.py 中的共享工具。

目录结构（<work_root> 为计算工作根，与脚本安装路径无关）:
  <work_root>/<A>/<B>/opt/       — 结构优化
  <work_root>/<A>/<B>/scf_ELF/   — ELF 计算
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

from vasp_common import (
    DEFAULT_PBE_LIB,
    PBS_FOOTER,
    PBS_HEADER,
    RelaxStructure,
    SCF_SUBDIR,
    assemble_potcar,
    parse_relax_in,
    write_poscar,
    write_run_script,
)


SCF_PBS_SCRIPT = "ELF.pbs"


SCF_INCAR = """SYSTEM = F
PREC = Accurate
ENCUT = 800
EDIFF = 1e-6
ISMEAR = 1
SIGMA = 0.02
LWAVE = FALSE
LCHARG = TRUE
LELF = TRUE
KSPACING = 0.02
KGAMMA = .TRUE.
NCORE = 4
"""


def setup_scf_scripts(
    base_dir: str | Path,
    overwrite: bool = True,
) -> Path:
    """建立 scf_ELF 目录并按需写入 ELF 计算脚本。

    ``overwrite=False`` 用于可重复执行的自动部署，避免覆盖用户已定制的
    队列、资源和 INCAR 参数；显式生成入口保留原有覆盖行为。
    """
    scf_dir = Path(base_dir) / SCF_SUBDIR
    script = scf_dir / SCF_PBS_SCRIPT
    if overwrite or not script.is_file():
        write_run_script(scf_dir, SCF_INCAR, filename=SCF_PBS_SCRIPT)
    return scf_dir


def deploy_poscar_to_scf(structure: RelaxStructure, base_dir: str | Path) -> Path:
    """Write POSCAR into scf_ELF only."""
    scf_dir = Path(base_dir) / SCF_SUBDIR
    scf_dir.mkdir(parents=True, exist_ok=True)
    return write_poscar(structure, scf_dir / "POSCAR")


def deploy_potcar_to_scf(
    elements: Sequence[str],
    base_dir: str | Path,
    pbe_lib: str | Path = DEFAULT_PBE_LIB,
) -> Dict[str, Dict[str, Any]]:
    """Assemble POTCAR into scf_ELF only."""
    scf_dir = Path(base_dir) / SCF_SUBDIR
    scf_dir.mkdir(parents=True, exist_ok=True)
    return assemble_potcar(elements, scf_dir / "POTCAR", pbe_lib=pbe_lib)


def deploy_scf_system(
    relax_in: str | Path,
    base_dir: str | Path,
    pbe_lib: str | Path = DEFAULT_PBE_LIB,
) -> Tuple[RelaxStructure, Dict[str, Dict[str, Any]]]:
    """Full deploy for scf: run script + POSCAR + POTCAR in scf_ELF."""
    structure = parse_relax_in(relax_in)
    setup_scf_scripts(base_dir, overwrite=False)
    deploy_poscar_to_scf(structure, base_dir)
    sources = deploy_potcar_to_scf(structure.elements, base_dir, pbe_lib=pbe_lib)
    return structure, sources
