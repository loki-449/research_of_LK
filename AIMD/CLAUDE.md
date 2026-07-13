# AIMD 后处理模块

## 模块定位
本目录存放从头算分子动力学（AIMD）后处理脚本，当前聚焦 **均方位移（MSD）与均方根位移（RMSD）** 分析。从 VASP AIMD 轨迹文件 `XDATCAR` 提取各元素的 MSD/RMSD 数据并绘图。

## 脚本清单

### 公共模块
| 脚本 | 功能 |
|------|------|
| `MSD&RMSD/msd_common.py` | 公共函数库（读 XDATCAR、计算 MSD、读写 .dat），供其他脚本调用 |

### 推荐使用（灵活版，元素自动识别）
| 脚本 | 功能 | 触发词 |
|------|------|--------|
| `MSD&RMSD/extract_msd_flex.py` | 从 XDATCAR 提取 MSD/RMSD，输出 .dat 表格 | "提取 MSD"、"extract msd" |
| `MSD&RMSD/plot_msd_flex.py` | 读取 .dat，自动识别元素列并绘制 MSD/RMSD 双子图 | "画 MSD 图"、"plot msd" |
| `MSD&RMSD/xdatcar_msd_flex.py` | 一键完成：计算 + 摘要 + 出图 | "MSD 一键分析"、"xdatcar msd" |
| `MSD&RMSD/plot_line_template.py` | 通用线性图模板，配置驱动，可复用于其他 .dat | "画折线图"、"line template" |

### 原版（保留，兼容旧流程）
| 脚本 | 功能 |
|------|------|
| `MSD&RMSD/extract_msd.py` | 数据提取（精简版） |
| `MSD&RMSD/xdatcar_msd.py` | 一体化计算与绘图 |
| `MSD&RMSD/xdatcar_msd_orig.py` | 早期完整实现 |
| `MSD&RMSD/plot_msd.py` | 绘图脚本，需手动配置元素样式 |

## 推荐工作流

### 流程 A：提取数据 + 自定义绘图
```bash
cd AIMD/MSD&RMSD

# 1. 提取数据（元素自动从 XDATCAR 读取）
python extract_msd_flex.py path/to/XDATCAR --dt 1.0 -o msd_data.dat

# 2. 快速出图
python plot_msd_flex.py msd_data.dat

# 3. 或用通用模板自定义
python plot_line_template.py msd_data.dat -o my_plot.png
```

### 流程 B：一键完成
```bash
cd AIMD/MSD&RMSD
python xdatcar_msd_flex.py path/to/XDATCAR --dt 1.0
```

## 输入规范
- **XDATCAR**：VASP AIMD 轨迹文件，格式为 VASP 5.x 标准输出
- **--dt**：AIMD 步长（fs），需与 INCAR 中 POTIM 一致
- **--elements**：可选筛选元素（空格分隔），默认全部
- **--element-order**：`file`（文件顺序）或 `alpha`（字母序）

## 输出格式
```
#       Time(ps)      H_MSD(A2)     Ag_MSD(A2)      H_RMSD(A)     Ag_RMSD(A)
      0.000000      0.000000      0.000000      0.000000      0.000000
    100.000000      0.123456      0.045678      0.351364      0.213728
```

## 依赖
```bash
pip install numpy matplotlib
```
- 仅数据提取只需 `numpy`
- 绘图需额外 `matplotlib`

## 注意事项
- 建议在 `AIMD/MSD&RMSD/` 目录下运行脚本
- `--dt` 必须与 VASP INCAR 的 `POTIM` 一致
- 灵活版脚本换 XDATCAR 无需修改任何代码，元素自动识别
- `plot_line_template.py` 通过顶部配置区修改子图/列/样式，可复用于非 MSD 数据
