#!/usr/bin/env python3
"""MSD/RMSD 绘图脚本 —— 所有可调参数集中在顶部，注释标注用途"""
import numpy as np

# ============================================================
# 输入文件配置
# ============================================================
DATAFILE = "msd_data.dat"    # extract_msd.py 输出的 .dat 文件

# ============================================================
# 图表尺寸与输出
# ============================================================
FIG_WIDTH  = 14.0            # 图总宽度 (inch)
FIG_HEIGHT = 6.0             # 图总高度 (inch)
DPI        = 200             # 分辨率
OUTPUT     = "msd_rmsd.png"  # 输出文件名

# ============================================================
# 字体配置（全局）
# ============================================================
FONT_FAMILY   = 'sans-serif'       # 字体族: 'serif','sans-serif','monospace'
FONT_SIZE     = 11                 # 基础字号
TITLE_SIZE    = 14                 # 标题字号
LABEL_SIZE    = 12                 # 轴标签字号
TICK_SIZE     = 10                 # 刻度数字字号
LEGEND_SIZE   = 9                  # 图例字号
LEGEND_FRAME  = True               # 图例是否带边框

# ============================================================
# 线条配置（按元素名）
# ============================================================
LINE_CONFIG = {
    'H':  {'color': '#2ca02c', 'width': 1.5, 'style': '-',  'marker': ''},
    'Ag': {'color': '#1f77b4', 'width': 1.5, 'style': '-',  'marker': ''},
    'Ba': {'color': '#ff7f0e', 'width': 1.5, 'style': '-',  'marker': ''},
}
# 对未列出的元素自动从 DEFAULT_COLORS 循环取色
DEFAULT_COLORS = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f']

# ============================================================
# 横坐标 (Time) 配置
# ============================================================
X_LABEL   = "Time (ps)"     # 横坐标标签文字
X_MIN     = None            # 横坐标下限 (None=auto)
X_MAX     = None            # 横坐标上限 (None=auto)
X_TICK    = None            # 横坐标刻度间隔 (None=auto)

# ============================================================
# 左图纵坐标 (MSD) 配置
# ============================================================
Y1_LABEL  = "MSD (Å²)"       # 纵坐标标签 (Å = A-ring)
Y1_MIN    = None            # 纵坐标下限 (None=auto)
Y1_MAX    = None            # 纵坐标上限 (None=auto)
Y1_TICK   = None            # 纵坐标刻度间隔 (None=auto)
Y1_TITLE  = "MSD"           # 左图标题

# ============================================================
# 右图纵坐标 (RMSD) 配置
# ============================================================
Y2_LABEL  = "RMSD (Å)"      # 纵坐标标签
Y2_MIN    = None            # 纵坐标下限 (None=auto)
Y2_MAX    = None            # 纵坐标上限 (None=auto)
Y2_TICK   = None            # 纵坐标刻度间隔 (None=auto)
Y2_TITLE  = "RMSD"          # 右图标题

# ============================================================
# 辅助线配置
# ============================================================
GRID_ALPHA   = 0.3           # 网格透明度 (0=不显示)
GRID_STYLE   = '--'          # 网格线型: '-' '--' ':' '-.'
GRID_LINEWIDTH = 0.5         # 网格线粗

# 水平/垂直参照虚线 (None=不画)
HLINE_Y      = None          # 如 0.5 -- 在对应值处画水平虚线
HLINE_STYLE  = '--'          # 虚线型
HLINE_COLOR  = 'gray'
HLINE_WIDTH  = 1.0

VLINE_X      = None          # 如 5.0 -- 在对应值处画垂直虚线
VLINE_STYLE  = '--'
VLINE_COLOR  = 'gray'
VLINE_WIDTH  = 1.0

# ============================================================
# 标识框 (annotation box)
# ============================================================
ANNOTATE_TEXT   = ""         # 标识框文字 (空='' 表示不显示)
                             # 如 'T = 100 K, P = 50 GPa'
ANNOTATE_POS    = (0.98, 0.95)  # 框锚点 (轴坐标，以轴为单位，0-1)
ANNOTATE_HA     = 'right'       # 水平对齐: 'left','center','right'
ANNOTATE_VA     = 'top'         # 垂直对齐: 'top','center','bottom'
ANNOTATE_BBOX   = True          # 是否带背景框
ANNOTATE_FONTSIZE = 10         # 标识框字号

# ============================================================
# 其他
# ============================================================
SHOW_TITLE  = True           # 是否显示子图标题
SAVEFIG_KW  = {}             # 传给 savefig 的额外参数 (如 {'transparent':True})
TIGHT_LAYOUT = True          # 是否启用 tight_layout

# ============================================================
# ============================================================
#  绘图主函数 (一般不需要修改以下内容)
# ============================================================
# ============================================================
def load_data(filepath):
    """从 .dat 文件加载数据，返回 dict {colname: array}"""
    data = {}
    with open(filepath) as f:
        for line in f:
            if line.startswith('#'):
                header = line[1:].strip().split()
                for h in header:
                    data[h] = []
            else:
                vals = list(map(float, line.strip().split()))
                for h, v in zip(header, vals):
                    data[h].append(v)
    return {k: np.array(v) for k, v in data.items()}

def parse_elements(colnames):
    """从列名列表中提取元素名"""
    elems = []
    for c in colnames:
        if c.endswith('_MSD(A2)'):
            elems.append(c.replace('_MSD(A2)', ''))
    return sorted(elems)  # 默认按字母排序，也可手动指定

def do_plot():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.rcParams['font.family'] = FONT_FAMILY
    plt.rcParams['font.size']   = FONT_SIZE

    data = load_data(DATAFILE)
    elems = parse_elements(list(data.keys()))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FIG_WIDTH, FIG_HEIGHT))

    time = data['Time(ps)']

    for ei, elem in enumerate(elems):
        cfg = LINE_CONFIG.get(elem, {
            'color': DEFAULT_COLORS[ei % len(DEFAULT_COLORS)],
            'width': 1.5, 'style': '-', 'marker': ''
        })
        msd_key  = f'{elem}_MSD(A2)'
        rmsd_key = f'{elem}_RMSD(A)'
        ax1.plot(time, data[msd_key],
                 color=cfg['color'], lw=cfg['width'], linestyle=cfg['style'],
                 marker=cfg['marker'], markersize=3, label=f'{elem}')
        ax2.plot(time, data[rmsd_key],
                 color=cfg['color'], lw=cfg['width'], linestyle=cfg['style'],
                 marker=cfg['marker'], markersize=3, label=f'{elem}')

    # -- 轴范围 --
    for ax, xlab, ylab in [(ax1, X_LABEL, Y1_LABEL), (ax2, X_LABEL, Y2_LABEL)]:
        ax.set_xlabel(xlab, fontsize=LABEL_SIZE)
        ax.set_ylabel(ylab, fontsize=LABEL_SIZE)
        ax.tick_params(labelsize=TICK_SIZE)
        if X_MIN is not None: ax.set_xlim(left=X_MIN)
        if X_MAX is not None: ax.set_xlim(right=X_MAX)

    if X_MIN is not None or X_MAX is not None:
        ax1.set_xlim(left=X_MIN, right=X_MAX)
        ax2.set_xlim(left=X_MIN, right=X_MAX)
    if X_TICK is not None:
        ax1.xaxis.set_major_locator(plt.MultipleLocator(X_TICK))
        ax2.xaxis.set_major_locator(plt.MultipleLocator(X_TICK))
    if Y1_MIN is not None or Y1_MAX is not None:
        ax1.set_ylim(bottom=Y1_MIN, top=Y1_MAX)
    if Y1_TICK is not None:
        ax1.yaxis.set_major_locator(plt.MultipleLocator(Y1_TICK))
    if Y2_MIN is not None or Y2_MAX is not None:
        ax2.set_ylim(bottom=Y2_MIN, top=Y2_MAX)
    if Y2_TICK is not None:
        ax2.yaxis.set_major_locator(plt.MultipleLocator(Y2_TICK))

    # -- 标题 --
    if SHOW_TITLE:
        ax1.set_title(Y1_TITLE, fontsize=TITLE_SIZE, fontweight='bold')
        ax2.set_title(Y2_TITLE, fontsize=TITLE_SIZE, fontweight='bold')

    # -- 网格 --
    if GRID_ALPHA > 0:
        ax1.grid(True, alpha=GRID_ALPHA, linestyle=GRID_STYLE, linewidth=GRID_LINEWIDTH)
        ax2.grid(True, alpha=GRID_ALPHA, linestyle=GRID_STYLE, linewidth=GRID_LINEWIDTH)

    # -- 辅助虚线 --
    if HLINE_Y is not None:
        for ax in (ax1, ax2):
            ax.axhline(y=HLINE_Y, color=HLINE_COLOR, linestyle=HLINE_STYLE, linewidth=HLINE_WIDTH)
    if VLINE_X is not None:
        for ax in (ax1, ax2):
            ax.axvline(x=VLINE_X, color=VLINE_COLOR, linestyle=VLINE_STYLE, linewidth=VLINE_WIDTH)

    # -- 图例 --
    for ax in (ax1, ax2):
        ax.legend(fontsize=LEGEND_SIZE, frameon=LEGEND_FRAME)

    # -- 标识框 --
    if ANNOTATE_TEXT:
        bbox = dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85) if ANNOTATE_BBOX else None
        ax1.annotate(ANNOTATE_TEXT, xy=ANNOTATE_POS, xycoords='axes fraction',
                     fontsize=ANNOTATE_FONTSIZE, ha=ANNOTATE_HA, va=ANNOTATE_VA, bbox=bbox)

    if TIGHT_LAYOUT:
        plt.tight_layout()
    plt.savefig(OUTPUT, dpi=DPI, **SAVEFIG_KW)
    print(f"Plot saved: {OUTPUT}")
    plt.close()

if __name__ == '__main__':
    do_plot()
