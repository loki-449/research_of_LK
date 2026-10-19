# AIMD 计算脚本

本目录用于存放 **从头算分子动力学（AIMD）** 相关的后处理脚本。

## 目录结构

```
calculation/
├── AIMD.md                 ← 本文件（AIMD 总览）
├── MSD&RMSD.md             ← MSD/RMSD 脚本详细说明
└── AIMD/
    └── MSD&RMSD/           ← MSD / RMSD 分析脚本
        ├── msd_common.py
        ├── extract_msd.py
        ├── extract_msd_flex.py
        ├── xdatcar_msd.py
        ├── xdatcar_msd_orig.py
        ├── xdatcar_msd_flex.py
        ├── plot_msd.py
        ├── plot_msd_flex.py
        └── plot_line_template.py
```

## 模块说明

| 子目录 | 功能 | 详细文档 |
|--------|------|----------|
| `AIMD/MSD&RMSD/` | 从 VASP XDATCAR 计算均方位移（MSD）与均方根位移（RMSD），支持按元素拆分与绘图 | [MSD&RMSD.md](MSD&RMSD.md) |

## 环境依赖

```bash
pip install numpy matplotlib
```

- 仅做数据提取（`extract_msd*.py`）时，只需 `numpy`
- 涉及绘图时需额外安装 `matplotlib`

## 快速开始（MSD/RMSD）

使用迁移后的规范入口（推荐；先按 `AIMD/deploy.env.example` 配置环境）：

```bash
# 推荐：从各体系 INCAR 自动读取 POTIM
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py \
  $AIMD_WORK_ROOT/<A>/AIMD/XDATCAR

# 或一步完成计算与出图
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/xdatcar_msd_flex.py \
  $AIMD_WORK_ROOT/<A>/AIMD/XDATCAR
```

旧目录 `AIMD/MSD&RMSD/` 的 `*_flex.py` 仅作兼容转发，不再运行独立算法副本。
更完整的参数说明、脚本对比与配置方法，见 [MSD&RMSD.md](MSD&RMSD.md)。

## 脚本版本选择

| 场景 | 推荐脚本 |
|------|----------|
| 换不同 XDATCAR / 元素组成会变 | `AIMD/scripts/MSD_RMSD/*_flex.py` 系列 |
| 固定体系、沿用旧配置 | 迁移到 `AIMD/scripts/MSD_RMSD/`；旧原版仅 Deprecated |
| 需要自定义多子图线性图 | `AIMD/scripts/MSD_RMSD/plot_line_template.py` |
