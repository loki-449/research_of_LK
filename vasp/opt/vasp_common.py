#!/usr/bin/env python3
"""
vasp_common.py — VASP ELF 工作流公共模块（共享工具 + opt 相关）

功能:
  - 解析 QE 计算文件夹命名（材料名 / 压强 / 温度）
  - 在 QE 目录中定位 relax.in
  - 解析 relax.in 结构信息
  - 生成 VASP PBS 提交脚本
  - POTCAR 库检索与择优（ZVAL 优先，日期次之）
  - POSCAR 生成
  - 体系文件夹建立（vasp/opt/<A>/<B>/opt_ELF）

scf_ELF 相关功能已拆分至 vasp/scf_ELF/scf_common.py。

赝势库默认路径（可在命令行用 --pbe-lib 或环境变量 PBE_LIB 覆盖）:
  /home/test1/hhy/basic/psudopotential/PAW-GGA-PBE

被以下脚本引用:
  vasp/opt/setup_elf_workflow.py   ELF 目录与 PBS 建立
  vasp/opt/make_poscar.py          POSCAR 生成
  vasp/opt/make_potcar.py          POTCAR 拼接
  vasp/opt/run_elf_batch.py        一键批量流程
  vasp/opt/submit_opt_elf.py       批量提交 opt_ELF PBS 任务
  vasp/scf_ELF/scf_common.py       scf_ELF 相关（导入本模块共享工具）
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ============================================================
# 赝势库配置（全局默认）
# ============================================================
DEFAULT_PBE_LIB = "/home/test1/hhy/basic/psudopotential/PAW-GGA-PBE"

COORD_KEYWORDS = frozenset({"crystal", "alat", "bohr", "angstrom"})

# ============================================================
# 子目录名称常量
# ============================================================
OPT_SUBDIR = "opt_ELF"
SCF_SUBDIR = "scf_ELF"


# ============================================================
# QE 体系文件夹解析
# ============================================================

@dataclass
class SystemInfo:
    """Parsed QE system folder metadata."""

    path: Path
    basename: str
    material: str
    pressure: str
    temperature: str

    @property
    def elf_subdir(self) -> str:
        return f"{self.material}/{self.pressure}"


def parse_system_name(basename: str) -> Optional[Tuple[str, str, str]]:
    """Parse folder name into (material, pressure, temperature).

    Rules match the original setup_elf.sh:
      - material    : substring before the first '-'
      - temperature : last numeric value followed by 'K'
      - pressure    : first numeric value in the middle segment

    Example: Ag-H-50GPa-300K -> ('Ag', '50', '300')
    """
    if "-" not in basename:
        return None

    material = basename.split("-", 1)[0]
    rest = basename[len(material) + 1 :]

    temp_match = re.search(r"([0-9.]+)K$", rest)
    if not temp_match:
        return None
    temperature = temp_match.group(1)

    middle = rest[: temp_match.start()]
    if middle.endswith("-"):
        middle = middle[:-1]

    pressure_match = re.search(r"([0-9.]+)", middle)
    if not pressure_match:
        return None
    pressure = pressure_match.group(1)

    if not material or not pressure or not temperature:
        return None
    return material, pressure, temperature


def find_qe_system_dirs(qe_dir: str | Path, pattern: str = "*GPa*") -> List[Path]:
    """Find first-level QE system directories matching pattern."""
    root = Path(qe_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"QE directory not found: {root}")
    return sorted(p for p in root.glob(pattern) if p.is_dir())


def parse_qe_system(path: str | Path) -> Optional[SystemInfo]:
    """Parse a QE system directory into SystemInfo."""
    p = Path(path)
    parsed = parse_system_name(p.name)
    if not parsed:
        return None
    material, pressure, temperature = parsed
    return SystemInfo(
        path=p,
        basename=p.name,
        material=material,
        pressure=pressure,
        temperature=temperature,
    )


# ============================================================
# relax.in 定位与解析
# ============================================================

def find_relax_in(system_dir: str | Path, max_depth: int = 3) -> Optional[Path]:
    """Locate relax.in under a QE system directory."""
    root = Path(system_dir)
    if not root.is_dir():
        return None

    direct = root / "relax.in"
    if direct.is_file():
        return direct

    for depth in range(1, max_depth + 1):
        pattern = "/".join(["*"] * depth) + "/relax.in"
        matches = sorted(root.glob(pattern))
        if matches:
            return matches[0]
    return None


def _split_section(text: str, start_key: str, end_keys: str | Sequence[str]) -> str:
    if start_key not in text:
        raise ValueError(f"Section '{start_key}' not found")
    block = text.split(start_key, 1)[1]
    if isinstance(end_keys, str):
        end_keys = [end_keys]

    cut = len(block)
    for end_key in end_keys:
        if end_key in block:
            cut = min(cut, block.index(end_key))
    return block[:cut]


@dataclass
class RelaxStructure:
    """Structure extracted from QE relax.in."""

    elements: List[str]
    counts: List[int]
    cell_lines: List[str]
    positions: List[Tuple[str, float, float, float]]


def parse_relax_in(relax_in: str | Path) -> RelaxStructure:
    """Parse QE relax.in into structure data for POSCAR generation."""
    text = Path(relax_in).read_text(encoding="utf-8", errors="replace")

    pos_block = _split_section(
        text, "ATOMIC_POSITIONS", ["K_POINTS", "ATOMIC_FORCES"]
    )
    pos_lines = [
        line.strip()
        for line in pos_block.strip().splitlines()
        if line.strip() and not line.strip().startswith("{")
    ]
    if pos_lines and pos_lines[0].lower() in COORD_KEYWORDS:
        pos_lines = pos_lines[1:]

    positions: List[Tuple[str, float, float, float]] = []
    for line in pos_lines:
        parts = line.split()
        if len(parts) >= 4:
            positions.append((parts[0], float(parts[1]), float(parts[2]), float(parts[3])))

    if not positions:
        raise ValueError(f"No atomic positions found in {relax_in}")

    elements: List[str] = []
    for elem, _, _, _ in positions:
        if elem not in elements:
            elements.append(elem)
    counts = [sum(1 for p in positions if p[0] == elem) for elem in elements]

    cell_block = _split_section(text, "CELL_PARAMETERS", "ATOMIC_POSITIONS")
    cell_lines: List[str] = []
    for line in cell_block.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("{"):
            continue
        parts = line.split()
        if len(parts) >= 3:
            cell_lines.append(line)
    cell_lines = cell_lines[:3]
    if len(cell_lines) != 3:
        raise ValueError(f"Expected 3 cell vectors in {relax_in}, got {len(cell_lines)}")

    return RelaxStructure(
        elements=elements,
        counts=counts,
        cell_lines=cell_lines,
        positions=positions,
    )


# ============================================================
# POSCAR 生成
# ============================================================

def write_poscar(structure: RelaxStructure, output: str | Path) -> Path:
    """Write VASP POSCAR from parsed relax.in structure."""
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "POSCAR",
        "1.00000000000000",
        *structure.cell_lines,
        " ".join(structure.elements),
        " ".join(str(c) for c in structure.counts),
        "Direct",
    ]
    for _, x, y, z in structure.positions:
        lines.append(f"  {x:.16f}  {y:.16f}  {z:.16f}")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def read_poscar_elements(poscar: str | Path) -> List[str]:
    """Read element order from POSCAR (line 6 in standard format)."""
    lines = Path(poscar).read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 6:
        raise ValueError(f"Invalid POSCAR format: {poscar}")
    return lines[5].split()


# ============================================================
# POTCAR 管理与择优
# ============================================================

def parse_potcar_zval(potcar: str | Path) -> float:
    """Extract ZVAL (valence electron count) from a single-element POTCAR."""
    text = Path(potcar).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines()[:30]:
        match = re.search(r"ZVAL\s*=\s*([0-9.]+)", line, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return 0.0


def parse_potcar_date(potcar: str | Path) -> datetime:
    """Parse generation date from POTCAR first line tail.

    Example first line: ' PAW_PBE H1.25 07Sep2000'
    """
    first = Path(potcar).read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
    match = re.search(r"(\d{2})([A-Za-z]{3})(\d{4})\s*$", first)
    if not match:
        return datetime.min

    day, month, year = match.groups()
    try:
        return datetime.strptime(f"{day}{month.title()}{year}", "%d%b%Y")
    except ValueError:
        return datetime.min


def parse_potcar_date_str(potcar: str | Path) -> str:
    """Return date string from POTCAR first line, e.g. '07Sep2000'."""
    first = Path(potcar).read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
    match = re.search(r"(\d{2}[A-Za-z]{3}\d{4})\s*$", first)
    return match.group(1) if match else "unknown"


@dataclass
class PotcarChoice:
    """Metadata for a selected single-element POTCAR."""

    element: str
    source_dir: str
    potcar_path: Path
    zval: float
    date: str


def find_potcar_candidates(element: str, pbe_lib: str | Path) -> List[Path]:
    """List candidate directories that may contain a single-element POTCAR.

    Supports common VASP library layouts:
      <lib>/H/            exact element name
      <lib>/H.25/         numeric dot suffix (typical for H)
      <lib>/Ba_sv/        semicore (_sv) or hard (_pv) variants
      <lib>/Li_pv/
    """
    lib = Path(pbe_lib)
    if not lib.is_dir():
        raise FileNotFoundError(f"PBE library not found: {lib}")

    candidates: List[Path] = []
    seen = set()

    def add_candidate(path: Path) -> None:
        key = str(path.resolve()) if path.exists() else str(path)
        if key not in seen:
            seen.add(key)
            candidates.append(path)

    exact = lib / element
    if exact.is_dir():
        add_candidate(exact)

    for child in sorted(lib.iterdir()):
        if not child.is_dir():
            continue
        name = child.name
        if name.startswith(f"{element}.") or name.startswith(f"{element}_"):
            add_candidate(child)

    return candidates


def select_best_potcar_file(candidates: Sequence[Path]) -> Optional[Path]:
    """Pick POTCAR with highest ZVAL; tie-break by newest date on line 1."""
    best_file: Optional[Path] = None
    best_key: Tuple[float, datetime] = (-1.0, datetime.min)

    for cand in candidates:
        potcar = cand / "POTCAR"
        if not potcar.is_file():
            continue
        zval = parse_potcar_zval(potcar)
        date = parse_potcar_date(potcar)
        key = (zval, date)
        if key > best_key:
            best_key = key
            best_file = potcar

    return best_file


def find_best_potcar(element: str, pbe_lib: str | Path) -> Path:
    """Pick the best POTCAR for an element from the pseudopotential library."""
    candidates = find_potcar_candidates(element, pbe_lib)
    best_file = select_best_potcar_file(candidates)

    if best_file is None:
        searched = ", ".join(p.name for p in candidates) or "(none)"
        raise FileNotFoundError(
            f"No POTCAR found for element '{element}' under {pbe_lib}. "
            f"Searched: {searched}"
        )

    return best_file


def choose_potcar(element: str, pbe_lib: str | Path) -> PotcarChoice:
    """Find best POTCAR and return selection metadata."""
    src = find_best_potcar(element, pbe_lib)
    return PotcarChoice(
        element=element,
        source_dir=src.parent.name,
        potcar_path=src,
        zval=parse_potcar_zval(src),
        date=parse_potcar_date_str(src),
    )


def copy_single_potcars(
    elements: Sequence[str],
    target_dir: str | Path,
    pbe_lib: str | Path = DEFAULT_PBE_LIB,
) -> Dict[str, Dict[str, Any]]:
    """Copy best POTCAR per element to <target>/<Elem>.POTCAR.

    Source files in the pseudopotential library are never renamed.
    Selection rule: max ZVAL first, then newest date on line 1.
    Returns mapping {element: {dir, zval, date}}.
    """
    out_dir = Path(target_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sources: Dict[str, Dict[str, Any]] = {}
    for elem in elements:
        choice = choose_potcar(elem, pbe_lib)
        dst = out_dir / f"{elem}.POTCAR"
        dst.write_bytes(choice.potcar_path.read_bytes())
        sources[elem] = {
            "dir": choice.source_dir,
            "zval": choice.zval,
            "date": choice.date,
        }
    return sources


def cat_potcar_in_order(
    elements: Sequence[str],
    target_dir: str | Path,
    output_name: str = "POTCAR",
    remove_singles: bool = True,
) -> Path:
    """Concatenate <Elem>.POTCAR files in element order into final POTCAR."""
    out_dir = Path(target_dir)
    final = out_dir / output_name

    with final.open("wb") as out_f:
        for elem in elements:
            single = out_dir / f"{elem}.POTCAR"
            if not single.is_file():
                raise FileNotFoundError(f"Missing single-element file: {single}")
            out_f.write(single.read_bytes())

    if remove_singles:
        for elem in elements:
            (out_dir / f"{elem}.POTCAR").unlink(missing_ok=True)

    return final


def assemble_potcar(
    elements: Sequence[str],
    output: str | Path,
    pbe_lib: str | Path = DEFAULT_PBE_LIB,
    keep_single_files: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """Assemble multi-element POTCAR: copy singles, then cat in order.

    Workflow (matches setup_elf.sh):
      1. cp <lib>/.../POTCAR  ->  <target>/<Elem>.POTCAR
      2. cat <Elem>.POTCAR ... ->  <target>/POTCAR
      3. remove <Elem>.POTCAR unless keep_single_files=True

    Returns mapping {element: source_directory_name}.
    """
    out = Path(output)
    target_dir = out.parent
    sources = copy_single_potcars(elements, target_dir, pbe_lib=pbe_lib)
    cat_potcar_in_order(
        elements,
        target_dir,
        output_name=out.name,
        remove_singles=not keep_single_files,
    )
    return sources


# ============================================================
# PBS 脚本与 INCAR 模板（共享部分）
# ============================================================

PBS_HEADER = """#!/bin/bash
#PBS -N epw-test
#PBS -l nodes=1:ppn=64
#PBS -q song
#PBS -j n
cd $PBS_O_WORKDIR
module add oneapi/mpi/latest > /dev/null 2>&1
module add oneapi/compiler/latest > /dev/null 2>&1
module add oneapi/mkl/latest > /dev/null 2>&1
module add gcc/9.1.0
module add intel/intel2018
module add oneapi/compiler oneapi/mpi oneapi/mkl vasp
cat > INCAR << EOF
"""

PBS_FOOTER = """EOF
mpirun -np 16 vasp_std >> log
"""

OPT_INCAR = """SYSTEM = Relaxation
PREC = Accurate
ENCUT = 800
EDIFF = 1e-6
ISMEAR = 1
SIGMA = 0.02
ISIF = 3
IBRION = 2
NSW = 200
EDIFFG = -0.01
LWAVE = FALSE
LCHARG = TRUE
NCORE = 4
KSPACING = 0.02
KGAMMA = .TRUE.
"""


# ============================================================
# 体系目录与工作目录管理（共享）
# ============================================================

def system_base_dir(elf_root: str | Path, material: str, pressure: str) -> Path:
    """Return ELF/<material>/<pressure>/ base path."""
    return Path(elf_root) / material / pressure


def get_work_dirs(base_dir: str | Path) -> Tuple[Path, Path]:
    """Return (opt_ELF, scf_ELF) paths under a system base directory."""
    base = Path(base_dir)
    return base / OPT_SUBDIR, base / SCF_SUBDIR


def write_run_script(
    target_dir: str | Path,
    incar: str,
    filename: str = "ELF.pbs",
) -> Path:
    """Write PBS submission script with given INCAR block."""
    out_dir = Path(target_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / filename
    out.write_text(PBS_HEADER + incar + PBS_FOOTER, encoding="utf-8")
    return out


# ============================================================
# opt_ELF 工作目录操作
# ============================================================

def setup_opt_scripts(base_dir: str | Path) -> Path:
    """Create opt_ELF directory and write opt (Relaxation) run script."""
    opt_dir = Path(base_dir) / OPT_SUBDIR
    write_run_script(opt_dir, OPT_INCAR)
    return opt_dir


def deploy_poscar_to_opt(structure: RelaxStructure, base_dir: str | Path) -> Path:
    """Write POSCAR into opt_ELF only."""
    opt_dir = Path(base_dir) / OPT_SUBDIR
    opt_dir.mkdir(parents=True, exist_ok=True)
    return write_poscar(structure, opt_dir / "POSCAR")


def deploy_potcar_to_opt(
    elements: Sequence[str],
    base_dir: str | Path,
    pbe_lib: str | Path = DEFAULT_PBE_LIB,
) -> Dict[str, Dict[str, Any]]:
    """Assemble POTCAR into opt_ELF only."""
    opt_dir = Path(base_dir) / OPT_SUBDIR
    opt_dir.mkdir(parents=True, exist_ok=True)
    return assemble_potcar(elements, opt_dir / "POTCAR", pbe_lib=pbe_lib)


def deploy_opt_system(
    relax_in: str | Path,
    base_dir: str | Path,
    pbe_lib: str | Path = DEFAULT_PBE_LIB,
) -> Tuple[RelaxStructure, Dict[str, Dict[str, Any]]]:
    """Full deploy for opt: run script + POSCAR + POTCAR in opt_ELF."""
    structure = parse_relax_in(relax_in)
    setup_opt_scripts(base_dir)
    deploy_poscar_to_opt(structure, base_dir)
    sources = deploy_potcar_to_opt(structure.elements, base_dir, pbe_lib=pbe_lib)
    return structure, sources


# ============================================================
# 向后兼容
# ============================================================

def write_elf_pbs(target_dir: str | Path, filename: str = "ELF.pbs") -> Path:
    """Backward-compatible alias: write relaxation script to given directory."""
    return write_run_script(target_dir, OPT_INCAR, filen