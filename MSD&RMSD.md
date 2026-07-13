# MSD / RMSD 分析脚本说明

脚本路径：`AIMD/MSD&RMSD/`

从 VASP AIMD 轨迹文件 `XDATCAR` 计算各元素的均方位移（MSD）和均方根位移（RMSD），并支持导出数据表与绘图。

---

## 脚本一览

### 公共模块

| 文件 | 说明 |
|------|------|
| `msd_common.py` | 公共函数库（读 XDATCAR、计算 MSD、读写 .dat），供其他脚本调用，一般不直接运行 |

### 灵活版（推荐，元素自动识别）

| 文件 | 说明 |
|------|------|
| `extract_msd_flex.py` | 从 XDATCAR 提取 MSD/RMSD，输出 `.dat` 表格 |
| `xdatcar_msd_flex.py` | 一步完成：计算 + 打印摘要 + 出图 |
| `plot_msd_flex.py` | 读取 `.dat`，自动识别元素列并绘制 MSD/RMSD 双子图 |
| `plot_line_template.py` | 通用简单线性图模板，配置驱动，可复用于其他 `.dat` 数据 |

### 原版（保留）

| 文件 | 说明 |
|------|------|
| `extract_msd.py` | 数据提取，元素自动识别但参数较少 |
| `xdatcar_msd.py` | 一体化计算与绘图（精简版） |
| `xdatcar_msd_orig.py` | 早期完整实现，含中文注释 |
| `plot_msd.py` | 绘图脚本，顶部集中配置；`LINE_CONFIG` 中元素样式需手动填写 |

---

## 推荐工作流

### 流程 A：提取数据 + 自定义绘图（最灵活）

```bash
cd AIMD/MSD&RMSD

# 1. 提取数据（元素自动从 XDATCAR 读取）
python extract_msd_flex.py ../path/to/XDATCAR --dt 1.0 -o msd_data.dat

# 2a. 快速出 MSD/RMSD 图
python plot_msd_flex.py msd_data.dat

# 2b. 或用通用模板，修改 plot_line_template.py 顶部配置后出图
python plot_line_template.py msd_data.dat -o my_plot.png
```

### 流程 B：一步完成

```bash
cd AIMD/MSD&RMSD
python xdatcar_msd_flex.py ../path/to/XDATCAR --dt 1.0
```

---

## 命令行参数

### extract_msd_flex.py

```
python extract_msd_flex.py [XDATCAR] [选项]

位置参数:
  XDATCAR               轨迹文件路径（默认: XDATCAR）

选项:
  --dt FLOAT            AIMD 步长，单位 fs（默认: 1.0）
  -o, --output PATH     输出 .dat 路径（默认: <文件名>_msd.dat）
  --stride INT          每隔 N 帧写一行（默认: 100）
  --elements E1 E2 ...  只导出指定元素（默认: 全部）
  --element-order       列顺序: file（文件顺序）或 alpha（字母序）
```

### xdatcar_msd_flex.py

```
python xdatcar_msd_flex.py [XDATCAR] [选项]

选项:
  --dt FLOAT            AIMD 步长，单位 fs（默认: 1.0）
  -o, --output PATH     输出图片路径（默认: <文件名>_msd_rmsd.png）
  --elements E1 E2 ...  只分析指定元素
  --element-order       file 或 alpha
  --no-plot             只计算，不画图
```

### plot_msd_flex.py

```
python plot_msd_flex.py [datafile] [-o output.png]

  datafile              输入 .dat（默认: msd_data.dat）
  -o, --output          输出图片（默认: <数据文件名>_msd_rmsd.png）
```

### plot_line_template.py

```
python plot_line_template.py [datafile] [-o output.png]
```

主要配置在脚本顶部「配置区」，运行前按需修改 `DATAFILE`、`PANELS`、`LINE_STYLE` 等变量。

---

## 输出数据格式

`extract_msd_flex.py` 生成的 `.dat` 文件示例：

```
#       Time(ps)      H_MSD(A2)     Ag_MSD(A2)      H_RMSD(A)     Ag_RMSD(A)
      0.000000      0.000000      0.000000      0.000000      0.000000
    100.000000      0.123456      0.045678      0.351364      0.213728
```

列名规则：

| 列名 | 含义 |
|------|------|
| `Time(ps)` | 时间（皮秒） |
| `<元素>_MSD(A2)` | 该元素均方位移（Å²） |
| `<元素>_RMSD(A)` | 该元素均方根位移（Å） |

---

## plot_line_template.py 配置说明

修改脚本顶部配置区即可复用，无需改动绘图引擎：

| 变量 | 用途 |
|------|------|
| `DATAFILE` | 输入数据文件 |
| `OUTPUT` | 输出图片文件名 |
| `PANELS` | 子图列表，每项含 `title`、`x_col`、`y_columns`、`ylabel` 等 |
| `LINE_STYLE` | 按图例标签覆盖颜色、线宽、线型（可选） |
| `DEFAULT_COLORS` | 未指定样式的系列自动循环取色 |
| `NCOLS` | 子图排列列数 |
| `ANNOTATE_TEXT` | 标注文字（如 `T = 300 K`） |

`y_columns` 支持通配符，例如 `"*_MSD(A2)"` 会自动匹配所有 MSD 列。

MSD 典型配置：

```python
PANELS = [
    {"title": "MSD",  "x_col": "Time(ps)", "y_columns": "*_MSD(A2)",  "ylabel": "MSD (A^2)"},
    {"title": "RMSD", "x_col": "Time(ps)", "y_columns": "*_RMSD(A)", "ylabel": "RMSD (A)"},
]
```

---

## 灵活版 vs 原版

| 对比项 | 灵活版 (`*_flex.py`) | 原版 |
|--------|----------------------|------|
| 元素识别 | 自动，换 XDATCAR 无需改脚本 | `plot_msd.py` 的 `LINE_CONFIG` 需手写元素名 |
| 命令行参数 | 完整（筛选元素、排序、输出路径等） | 较简单 |
| 通用绘图 | `plot_line_template.py` 可复用于其他数据 | 仅 MSD 专用 |
| 适用场景 | 多体系、频繁换 XDATCAR | 固定体系、沿用旧习惯 |

---

## 注意事项

1. **运行目录**：建议在 `AIMD/MSD&RMSD/` 下执行，或保证该目录在 Python 路径中（脚本间通过 `from msd_common import ...` 互相引用）。
2. **时间步长 `--dt`**：需与 VASP INCAR 中 `POTIM`（fs）一致，否则横轴时间不准确。
3. **XDATCAR 路径**：可使用相对路径或绝对路径指向任意位置的轨迹文件。
4. **依赖**：`pip install numpy matplotlib`（仅提取数据时 matplotlib 非必须）。
