# MSD_RMSD — 均方位移 / 均方根位移后处理

从 `$AIMD_WORK_ROOT/<A>/AIMD/XDATCAR` 提取 MSD/RMSD，结果汇总到工作根下专用目录。

## 依赖

```bash
pip install numpy matplotlib   # 仅提取可只要 numpy
```

## 数据布局

```
$AIMD_WORK_ROOT/
├── MSD_data_for_origin/<A>_msd_data.dat
├── MSD_png/<A>_msd_rmsd.png
└── <A>/
    ├── opt/  scf-MD/  AIMD/{XDATCAR,INCAR}
    └── msd_data.dat          # 中间文件，默认 mv 走
```

## dt（时间步）

未指定 `--dt` 时读 `$WR/<A>/AIMD/INCAR` 中的 **POTIM**（fs）。  
`Time(ps) = frame * POTIM / 1000`。POTIM 读错 → 时间轴整体缩放错误。

## 推荐命令

```bash
source /path/to/AIMD/deploy.env

# 单体系
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py \
  $AIMD_WORK_ROOT/<A>/AIMD/XDATCAR

# 批量（默认不出图）
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py --with-plot

# 绘图（读汇总 .dat）
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/plot_msd_flex.py \
  --work-root $AIMD_WORK_ROOT --system-dir $AIMD_WORK_ROOT/<A>
```

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `extract_msd_flex.py` | 提取 + 默认 publish |
| `run_msd_batch.py` | 批量提取 |
| `plot_msd_flex.py` | 画 MSD/RMSD |
| `xdatcar_msd_flex.py` | 一键摘要(+图) |
| `plot_line_template.py` | 通用折线模板 |

## 故障排查

| 现象 | 处理 |
|------|------|
| POTIM not found | 在 `AIMD/INCAR` 写 `POTIM = ...` 或传 `--dt` |
| SCR 空导致路径异常 | `source deploy.env` |
| 无 XDATCAR | 确认 `$WR/<A>/AIMD/XDATCAR` |
