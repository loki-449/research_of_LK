#!/usr/bin/env python3
"""
msd_common.py — MSD/RMSD 公共模块（供 flex 脚本调用，一般不直接运行）

功能:
  - 读取 VASP XDATCAR，按元素计算 MSD/RMSD
  - 读写 .dat；从 AIMD/INCAR 解析 POTIM；产物 mkdir + mv 汇总

列名约定: Time(ps) / <元素>_MSD(A2) / <元素>_RMSD(A)

dt 备注:
  POTIM（fs）决定 Time(ps)=frame*POTIM/1000；读错会整体拉伸时间轴。
  详见 AIMD_WORKFLOW.md / AIMD_DEPLOY_SPEC.md。
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from path_config import RESULT_DAT_DIR, RESULT_PNG_DIR, SKIP_DIR_NAMES

MSD_SUFFIX = "_MSD(A2)"
RMSD_SUFFIX = "_RMSD(A)"
LOCAL_DAT_NAME = "msd_data.dat"
AIMD_SUBDIR = "AIMD"


def read_xdatcar(path: str | Path) -> Tuple[np.ndarray, List[str]]:
    """Read VASP XDATCAR and return (positions, element_map)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    scale = float(lines[1].strip())
    lattice = np.array([list(map(float, line.split())) for line in lines[2:5]]) * scale
    elements_raw = lines[5].split()
    counts = list(map(int, lines[6].split()))
    n_atoms = sum(counts)

    elem_map: List[str] = []
    for elem, count in zip(elements_raw, counts):
        elem_map.extend([elem] * count)

    frames = []
    idx = 7
    while idx < len(lines):
        line = lines[idx].strip().lower()
        if line.startswith(("direct", "cart")):
            keyword = lines[idx].strip()
            idx += 1
            coords = []
            for _ in range(n_atoms):
                if idx >= len(lines):
                    break
                coords.append([float(x) for x in lines[idx].split()[:3]])
                idx += 1
            pos = np.array(coords)
            if keyword.lower().startswith("direct"):
                pos = pos @ lattice
            frames.append(pos)
        else:
            idx += 1

    if not frames:
        raise ValueError(f"No trajectory frames found in {path}")

    return np.array(frames), elem_map


def unique_elements(elem_map: List[str], order: str = "file") -> List[str]:
    if order == "alpha":
        return sorted(set(elem_map))
    seen: List[str] = []
    for elem in elem_map:
        if elem not in seen:
            seen.append(elem)
    return seen


def compute_msd_by_element(
    positions: np.ndarray,
    timestep_fs: float,
    elem_map: List[str],
    elements: List[str] | None = None,
) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Compute per-element MSD/RMSD relative to the first frame."""
    n_steps = positions.shape[0]
    t_ps = np.arange(n_steps) * timestep_fs / 1000.0

    if elements is None:
        elements = unique_elements(elem_map, order="file")
    else:
        unknown = sorted(set(elements) - set(elem_map))
        if unknown:
            raise ValueError(f"Unknown elements in XDATCAR: {unknown}")

    results: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for elem in elements:
        idxs = [i for i, name in enumerate(elem_map) if name == elem]
        sub = positions[:, idxs, :]
        ref = sub[0]
        msd = np.array(
            [np.mean(np.sum((sub[t] - ref) ** 2, axis=1)) for t in range(n_steps)]
        )
        results[elem] = (t_ps.copy(), msd, np.sqrt(msd))
    return results


def results_to_table(
    results: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]],
) -> Dict[str, np.ndarray]:
    elems = list(results.keys())
    t_ps = results[elems[0]][0]
    data = {"Time_ps": t_ps}
    for elem in elems:
        _, msd, rmsd = results[elem]
        data[f"{elem}_MSD"] = msd
        data[f"{elem}_RMSD"] = rmsd
    return data


def write_dat(
    data: Dict[str, np.ndarray],
    outpath: str | Path,
    stride: int = 1,
    element_order: List[str] | None = None,
) -> Path:
    if stride < 1:
        raise ValueError(f"stride must be >= 1, got {stride}")

    out = Path(outpath)
    out.parent.mkdir(parents=True, exist_ok=True)
    if element_order is None:
        element_order = [k.replace("_MSD", "") for k in data if k.endswith("_MSD")]

    cols = ["Time(ps)"]
    cols.extend(f"{elem}{MSD_SUFFIX}" for elem in element_order)
    cols.extend(f"{elem}{RMSD_SUFFIX}" for elem in element_order)

    n = len(data["Time_ps"])
    with out.open("w", encoding="utf-8") as f:
        f.write("# " + "  ".join(f"{c:>14s}" for c in cols) + "\n")
        for i in range(0, n, stride):
            vals = [data["Time_ps"][i]]
            vals.extend(data[f"{elem}_MSD"][i] for elem in element_order)
            vals.extend(data[f"{elem}_RMSD"][i] for elem in element_order)
            f.write("  ".join(f"{v:14.6f}" for v in vals) + "\n")

    print(
        f"Data written to {out} "
        f"({(n + stride - 1) // stride} rows, {len(element_order)} elements: {element_order})"
    )
    return out


def load_dat(filepath: str | Path) -> Dict[str, np.ndarray]:
    data: Dict[str, List[float]] = {}
    header: List[str] = []
    with open(filepath, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("#"):
                header = line[1:].strip().split()
                for col in header:
                    data[col] = []
            else:
                vals = list(map(float, line.strip().split()))
                for col, val in zip(header, vals):
                    data[col].append(val)
    return {k: np.array(v) for k, v in data.items()}


def parse_elements_from_columns(columns: List[str], suffix: str = MSD_SUFFIX) -> List[str]:
    elems = []
    for col in columns:
        if col.endswith(suffix):
            elems.append(col[: -len(suffix)])
    return elems


def match_columns(columns: List[str], pattern: str) -> List[str]:
    regex = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
    return [col for col in columns if re.fullmatch(regex, col)]


# ---------------------------------------------------------------------------
# 工作根布局 / POTIM / 汇总 mv
# ---------------------------------------------------------------------------

def system_dir_from_xdatcar(xdatcar: str | Path) -> Path:
    """.../<A>/AIMD/XDATCAR → <A>。"""
    p = Path(xdatcar).resolve()
    if p.parent.name == AIMD_SUBDIR:
        return p.parent.parent
    return p.parent


def aimd_dir_of(system_dir: str | Path) -> Path:
    return Path(system_dir) / AIMD_SUBDIR


def read_potim_from_incar(incar_path: str | Path) -> float:
    """从 INCAR 解析 POTIM（fs）。"""
    text = Path(incar_path).read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].split("!", 1)[0].strip()
        if not line:
            continue
        # POTIM = 1.0 或 POTIM=1.0
        m = re.match(r"POTIM\s*=\s*([0-9.+-Ee]+)", line, re.IGNORECASE)
        if m:
            return float(m.group(1))
    raise FileNotFoundError(
        f"POTIM not found in {incar_path}. "
        "Set POTIM in AIMD/INCAR or pass --dt explicitly."
    )


def resolve_dt(
    aimd_dir: str | Path,
    cli_dt: Optional[float] = None,
) -> Tuple[float, str]:
    """返回 (dt_fs, source_desc)。CLI 优先；否则读 AIMD/INCAR 的 POTIM。"""
    aimd = Path(aimd_dir)
    incar = aimd / "INCAR"
    if cli_dt is not None:
        src = f"CLI --dt={cli_dt}"
        if incar.is_file():
            try:
                potim = read_potim_from_incar(incar)
                if abs(potim - cli_dt) > 1e-12:
                    print(
                        f"  WARNING: --dt={cli_dt} differs from INCAR POTIM={potim} "
                        f"({incar}); using CLI value."
                    )
            except FileNotFoundError:
                pass
        return float(cli_dt), src

    if not incar.is_file():
        raise FileNotFoundError(
            f"No --dt given and INCAR missing: {incar}. "
            "Cannot resolve timestep."
        )
    potim = read_potim_from_incar(incar)
    return potim, f"INCAR POTIM={potim} ({incar})"


def iter_aimd_xdatcars(work_root: str | Path) -> List[Path]:
    """列出 $WR/*/AIMD/XDATCAR，跳过汇总目录名。"""
    root = Path(work_root)
    found: List[Path] = []
    if not root.is_dir():
        return found
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIR_NAMES:
            continue
        xdat = child / AIMD_SUBDIR / "XDATCAR"
        if xdat.is_file():
            found.append(xdat)
    return found


def ensure_result_dirs(work_root: str | Path) -> Tuple[Path, Path]:
    root = Path(work_root)
    dat_dir = root / RESULT_DAT_DIR
    png_dir = root / RESULT_PNG_DIR
    dat_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    return dat_dir, png_dir


def local_dat_path(system_dir: str | Path) -> Path:
    return Path(system_dir) / LOCAL_DAT_NAME


def published_dat_path(work_root: str | Path, system_a: str) -> Path:
    return Path(work_root) / RESULT_DAT_DIR / f"{system_a}_msd_data.dat"


def published_png_path(work_root: str | Path, system_a: str) -> Path:
    return Path(work_root) / RESULT_PNG_DIR / f"{system_a}_msd_rmsd.png"


def publish_file(src: str | Path, dest: str | Path, keep_local: bool = False) -> Path:
    """将产物移到汇总路径（shutil.move ≡ mv）。"""
    src_p = Path(src)
    dest_p = Path(dest)
    dest_p.parent.mkdir(parents=True, exist_ok=True)
    if not src_p.is_file():
        raise FileNotFoundError(f"Cannot publish missing file: {src_p}")
    if dest_p.exists():
        dest_p.unlink()
    if keep_local:
        shutil.copy2(src_p, dest_p)
        print(f"  copied -> {dest_p} (kept local {src_p})")
    else:
        shutil.move(str(src_p), str(dest_p))
        print(f"  mv -> {dest_p}")
    return dest_p


def publish_dat(
    src_dat: str | Path,
    work_root: str | Path,
    system_a: str,
    keep_local: bool = False,
) -> Path:
    ensure_result_dirs(work_root)
    return publish_file(
        src_dat, published_dat_path(work_root, system_a), keep_local=keep_local
    )


def publish_png(
    src_png: str | Path,
    work_root: str | Path,
    system_a: str,
    keep_local: bool = False,
) -> Path:
    ensure_result_dirs(work_root)
    return publish_file(
        src_png, published_png_path(work_root, system_a), keep_local=keep_local
    )


def resolve_dat_for_plot(
    work_root: str | Path | None,
    system_a: str | None,
    datafile: str | Path | None,
) -> Path:
    """优先汇总目录，其次 <A>/msd_data.dat，再否则 datafile。"""
    if datafile:
        p = Path(datafile)
        if p.is_file():
            return p
    if work_root and system_a:
        pub = published_dat_path(work_root, system_a)
        if pub.is_file():
            return pub
        local = local_dat_path(Path(work_root) / system_a)
        if local.is_file():
            return local
    raise FileNotFoundError(
        "No .dat found. Provide datafile or --system-dir / --work-root + system."
    )
