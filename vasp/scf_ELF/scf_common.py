#!/usr/bin/env python3
"""
scf_common.py — ELF scf 计算公共模块

功能:
  - SCF + ELF 计算的 INCAR 模板与 PBS 脚本生成
  - scf_ELF 目录管理与部署

依赖 vasp/opt/vasp_common.py 中的共享工具（解析 relax.in、赝势库等）。

目录结构:
  vasp/opt/<A>/<B>/opt_ELF/       — 结构优化（由 vasp_common 管理）
  vasp/scf_ELF/<A>/<B>/scf_ELF/   — ELF 计算（由本模块管理）
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

# 将 vasp/opt/ 加入路径以导入 vasp_common
_OPT_DIR = Path(__file__).resolve().parent.parent / "opt"
if str(_OPT_DIR) not in sys.path:
    sys.path.insert(0, str(_OPT_DIR))

from vasp_common import (  # noqa: E402
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


# ============================================================
# SCF + ELF INCAR
# ============================================================

SCF_INCAR = """SYSTEM = F
PREC = Accurate
ENCUT = 800
EDIFF = 1e-6
ISMEAR = 1
SIGMA = 0.02
LWAVE = FALSE
LCHARG = TRUE
LELF = TRUE
KSPACING = 0.03
KGAMMA = .TRUE.
NCORE = 4
"""


# ============================================================
# scf_ELF 工作目录操作
# ============================================================

def setup_scf_scripts(base_dir: str | Path) -> Path:
    """Create scf_ELF directory and write scf (LELF=TRUE) run script."""
    scf_dir = Path(base_dir) / SCF_SUBDIR
    write_run_script(scf_dir, SCF_INCAR)
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
    setup_scf_scripts(base_dir)
    deploy_poscar_to_scf(structure, base_dir)
    sources = deploy_potcar_to_scf(structure.elements, base_dir, pbe_lib=pbe_lib)
    return structure, source