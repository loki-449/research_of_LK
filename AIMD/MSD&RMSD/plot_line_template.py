#!/usr/bin/env python3
"""
plot_line_template.py — 通用简单线性图模板（配置驱动，可复用）

用途:
  读取 comment-header 格式的 .dat 数据文件，按顶部配置块绘制一个或多个子图。
  不限于 MSD，任何「X 列 + 若干 Y 列」的表格数据均可使用。

设计原则:
  - 只修改下方「配置区」即可复用，一般无需改动绘图引擎代码
  - y_columns 支持通配符（如 *_MSD(A2)），自动匹配列名
  - 未在 LINE_STYLE 中列出的系列，自动从 DEFAULT_COLORS 循环取色

依赖:
  pip install numpy matplotlib

基本用法:
  # 方式1: 修改下方 DATAFILE / PANELS 等配置后运行
  python plot_line_template.py

  # 方式2: 命令行指定文件（配置区其余项仍生效）
  python plot_line_template.py msd_data.dat -o my_plot.png

配置说明（修改下方对应变量）:
  DATAFILE      输入数据文件路径
  OUTPUT        输出图片文件名
  PANELS        子图列表，每个子图定义 title / x_col / y_columns / ylabel 等
                y_columns 可为通配符字符串（如 "*_MSD(A2)"）或显式列名列表
  LINE_STYLE    按图例标签覆盖线条颜色、线宽、线型（可选）
  NCOLS         子图排列列数
  ANNOTATE_TEXT 在指定子图上添加标注文字（如 'T = 300 K'）

MSD 典型配置示例:
  DATAFILE = "msd_data.dat"
  PANELS = [
      {"title": "MSD",  "x_col": "Time(ps)", "y_columns": "*_MSD(A2)",  "ylabel": "MSD (A^2)"},
      {"title": "RMSD", "x_col": "Time(ps)", "y_columns": "*_RMSD(A)", "ylabel": "RMSD (A)"},
  ]

推荐工作流:
  python extract_msd_flex.py XDATCAR -o msd_data.dat
  # 按需修改本文件顶部配置
  python plot_line_template.py

若只需快速画 MSD 图、不想手动配 PANELS，可直接用 plot_msd_flex.py。
"""
from __future__ import annotations

import argparse
import re
from typing import Any, Dict, List, Optional

import numpy as np

from msd_common import load_dat, match_columns

# ============================================================
# 1) Data source
# ============================================================
DATAFILE = "msd_data.dat"

# ============================================================
# 2) Figure output
# ============================================================
OUTPUT = "line_plot.png"
FIG_WIDTH = 14.0
FIG_HEIGHT = 6.0
DPI = 200
NCOLS = 2                    # number of subplot columns
TIGHT_LAYOUT = True
SAVEFIG_KW: Dict[str, Any] = {}

# ============================================================
# 3) Global style
# ============================================================
FONT_FAMILY = "sans-serif"
FONT_SIZE = 11
TITLE_SIZE = 14
LABEL_SIZE = 12
TICK_SIZE = 10
LEGEND_SIZE = 9
LEGEND_FRAME = True
SHOW_TITLE = True

GRID_ALPHA = 0.3
GRID_STYLE = "--"
GRID_LINEWIDTH = 0.5

DEFAULT_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
]

# Optional per-label style overrides. Unknown labels auto-cycle DEFAULT_COLORS.
LINE_STYLE: Dict[str, Dict[str, Any]] = {
    # "H":  {"color": "#2ca02c", "width": 1.5, "style": "-", "marker": ""},
}

# ============================================================
# 4) Panel definitions (the main switchable part)
# ============================================================
# Each panel draws one subplot.
# Required keys: title, x_col, y_columns
# y_columns supports:
#   - explicit list: ["H_MSD(A2)", "Ag_MSD(A2)"]
#   - wildcard text: "*_MSD(A2)" or "Time(ps)" is NOT allowed here
# Optional keys: xlabel, ylabel, xlim, ylim, xticks, yticks, hline, vline
PANELS: List[Dict[str, Any]] = [
    {
        "title": "MSD",
        "x_col": "Time(ps)",
        "y_columns": "*_MSD(A2)",
        "ylabel": "MSD (A^2)",
    },
    {
        "title": "RMSD",
        "x_col": "Time(ps)",
        "y_columns": "*_RMSD(A)",
        "ylabel": "RMSD (A)",
    },
]

# Shared axis label for x (used when panel xlabel is omitted)
X_LABEL = "Time (ps)"

# ============================================================
# 5) Annotation (optional)
# ============================================================
ANNOTATE_TEXT = ""
ANNOTATE_POS = (0.98, 0.95)
ANNOTATE_HA = "right"
ANNOTATE_VA = "top"
ANNOTATE_BBOX = True
ANNOTATE_FONTSIZE = 10
ANNOTATE_PANEL = 0           # which panel index receives the annotation box

# ============================================================
# Plot engine
# ============================================================
def _label_from_column(col: str) -> str:
    for suffix in ("_MSD(A2)", "_RMSD(A)"):
        if col.endswith(suffix):
            return col[: -len(suffix)]
    return col


def _resolve_y_columns(all_columns: List[str], spec) -> List[str]:
    if isinstance(spec, str):
        return match_columns(all_columns, spec)
    if isinstance(spec, list):
        missing = [c for c in spec if c not in all_columns]
        if missing:
            raise ValueError(f"Columns not found in data file: {missing}")
        return spec
    raise TypeError("y_columns must be a wildcard string or explicit column list")


def _line_cfg(label: str, index: int) -> Dict[str, Any]:
    if label in LINE_STYLE:
        return LINE_STYLE[label]
    return {
        "color": DEFAULT_COLORS[index % len(DEFAULT_COLORS)],
        "width": 1.5,
        "style": "-",
        "marker": "",
    }


def _apply_axis_limits(ax, limits, tick_key: str) -> None:
    import matplotlib.pyplot as plt

    if not limits:
        return
    lo, hi = limits
    if lo is not None or hi is not None:
        ax.set_xlim(left=lo, right=hi) if tick_key == "x" else ax.set_ylim(bottom=lo, top=hi)
    tick = limits[2] if len(limits) > 2 else None
    if tick is not None:
        locator = plt.MultipleLocator(tick)
        if tick_key == "x":
            ax.xaxis.set_major_locator(locator)
        else:
            ax.yaxis.set_major_locator(locator)


def do_plot(
    datafile: str = DATAFILE,
    output: str = OUTPUT,
    panels: Optional[List[Dict[str, Any]]] = None,
) -> str:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = FONT_FAMILY
    plt.rcParams["font.size"] = FONT_SIZE

    data = load_dat(datafile)
    columns = list(data.keys())
    panel_defs = panels or PANELS

    n_panels = len(panel_defs)
    nrows = (n_panels + NCOLS - 1) // NCOLS
    fig, axes = plt.subplots(nrows, NCOLS, figsize=(FIG_WIDTH, FIG_HEIGHT))
    axes_list = np.atleast_1d(axes).ravel().tolist()

    for pi, panel in enumerate(panel_defs):
        ax = axes_list[pi]
        x_col = panel["x_col"]
        if x_col not in data:
            raise ValueError(f"x_col '{x_col}' not found in {datafile}")

        y_cols = _resolve_y_columns(columns, panel["y_columns"])
        if not y_cols:
            raise ValueError(
                f"No y columns resolved for panel '{panel.get('title', pi)}' "
                f"from spec: {panel['y_columns']}"
            )

        x = data[x_col]
        for yi, y_col in enumerate(y_cols):
            label = _label_from_column(y_col)
            cfg = _line_cfg(label, yi)
            ax.plot(
                x,
                data[y_col],
                color=cfg["color"],
                lw=cfg["width"],
                linestyle=cfg["style"],
                marker=cfg.get("marker", ""),
                markersize=cfg.get("markersize", 3),
                label=label,
            )

        ax.set_xlabel(panel.get("xlabel", X_LABEL), fontsize=LABEL_SIZE)
        ax.set_ylabel(panel.get("ylabel", ""), fontsize=LABEL_SIZE)
        ax.tick_params(labelsize=TICK_SIZE)

        if SHOW_TITLE:
            ax.set_title(panel.get("title", ""), fontsize=TITLE_SIZE, fontweight="bold")

        if GRID_ALPHA > 0:
            ax.grid(True, alpha=GRID_ALPHA, linestyle=GRID_STYLE, linewidth=GRID_LINEWIDTH)

        _apply_axis_limits(ax, panel.get("xlim"), "x")
        _apply_axis_limits(ax, panel.get("ylim"), "y")

        if panel.get("hline") is not None:
            ax.axhline(y=panel["hline"], color="gray", linestyle="--", linewidth=1.0)
        if panel.get("vline") is not None:
            ax.axvline(x=panel["vline"], color="gray", linestyle="--", linewidth=1.0)

        ax.legend(fontsize=LEGEND_SIZE, frameon=LEGEND_FRAME)

    for ax in axes_list[n_panels:]:
        ax.set_visible(False)

    if ANNOTATE_TEXT and 0 <= ANNOTATE_PANEL < n_panels:
        bbox = (
            dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85)
            if ANNOTATE_BBOX
            else None
        )
        axes_list[ANNOTATE_PANEL].annotate(
            ANNOTATE_TEXT,
            xy=ANNOTATE_POS,
            xycoords="axes fraction",
            fontsize=ANNOTATE_FONTSIZE,
            ha=ANNOTATE_HA,
            va=ANNOTATE_VA,
            bbox=bbox,
        )

    if TIGHT_LAYOUT:
        plt.tight_layout()
    plt.savefig(output, dpi=DPI, **SAVEFIG_KW)
    plt.close()
    print(f"Plot saved: {output}")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Draw simple line plots from a comment-header .dat file."
    )
    parser.add_argument(
        "datafile",
        nargs="?",
        default=DATAFILE,
        help=f"Input .dat file (default: {DATAFILE})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=OUTPUT,
        help=f"Output image (default: {OUTPUT})",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    do_plot(datafile=args.datafile, output=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
