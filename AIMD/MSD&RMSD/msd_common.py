#!/usr/bin/env python3
"""
msd_common.py — MSD/RMSD 公共模块（供其他 flex 脚本调用，一般不直接运行）

功能:
  - 读取 VASP XDATCAR，自动解析元素种类与原子坐标
  - 按元素计算 MSD / RMSD
  - 读写 comment-header 格式的 .dat 数据表

被以下脚本引用:
  extract_msd_flex.py   数据提取
  xdatcar_msd_flex.py   计算 + 绘图
  plot_line_template.py 通用线性图
  plot_msd_flex.py      MSD 专用绘图

列名约定:
  Time(ps)          时间列
  <元素>_MSD(A2)    均方位移
  <元素>_RMSD(A)    均方根位移
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

import numpy as np

MSD_SUFFIX = "_MSD(A2)"
RMSD_SUFFIX = "_RMSD(A)"


def read_xdatcar(path: str) -> Tuple[np.ndarray, List[str]]:
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
    """Return unique element names.

    order:
      - 'file'   : preserve first-seen order in XDATCAR
      - 'alpha'  : alphabetical sort
    """
    if order == "alpha":
        return sorted(set(elem_map))

    seen = []
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
    """Convert MSD results dict to flat column dict for .dat output."""
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
    outpath: str,
    stride: int = 1,
    element_order: List[str] | None = None,
) -> None:
    """Write MSD/RMSD table to a comment-header .dat file."""
    if element_order is None:
        element_order = [k.replace("_MSD", "") for k in data if k.endswith("_MSD")]

    cols = ["Time(ps)"]
    cols.extend(f"{elem}{MSD_SUFFIX}" for elem in element_order)
    cols.extend(f"{elem}{RMSD_SUFFIX}" for elem in element_order)

    n = len(data["Time_ps"])
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("# " + "  ".join(f"{c:>14s}" for c in cols) + "\n")
        for i in range(0, n, stride):
            vals = [data["Time_ps"][i]]
            vals.extend(data[f"{elem}_MSD"][i] for elem in element_order)
            vals.extend(data[f"{elem}_RMSD"][i] for elem in element_order)
            f.write("  ".join(f"{v:14.6f}" for v in vals) + "\n")

    print(
        f"Data written to {outpath} "
        f"({(n + stride - 1) // stride} rows, {len(element_order)} elements: {element_order})"
    )


def load_dat(filepath: str) -> Dict[str, np.ndarray]:
    """Load comment-header .dat file into {column: array}."""
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
    """Extract element names from MSD/RMSD column names."""
    elems = []
    for col in columns:
        if col.endswith(suffix):
            elems.append(col[: -len(suffix)])
    return elems


def match_columns(columns: List[str], pattern: str) -> List[str]:
    """Match column names with shell-style wildcard pattern."""
    regex = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
    return [col for col in columns if re.fullmatch(regex, col)]
