# AIMD 后处理模块

## 模块定位
从头算分子动力学（AIMD）后处理，当前聚焦 **MSD / RMSD**。  
脚本安装于 `scripts/`，数据在 `$AIMD_WORK_ROOT`（与 VASP 环境变量分离）。

## 开发前
遵守根 `README.md` 四步；**上手优先**根目录 `AIMD_QUICKSTART.md`；规格见 `AIMD_DEPLOY_SPEC.md`；用法见 `AIMD_WORKFLOW.md`。

## 目录

```
AIMD/
├── deploy.env.example
├── README.md / AIMD_WORKFLOW.md / AIMD_DEPLOY_SPEC.md
├── example/                 ← MVP 样例（放 XDATCAR）
├── scripts/
│   ├── lib/
│   ├── MSD_RMSD/            ← 推荐入口
│   └── compat/              ← 旧版 Deprecated
└── MSD&RMSD/                ← 遗留跳转（勿再开发）
```

## 触发词
"提取 MSD"、"plot msd"、"XDATCAR"、"均方位移"、"AIMD 后处理"

## 推荐工作流

```bash
source AIMD/deploy.env
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py \
  $AIMD_WORK_ROOT/<A>/AIMD/XDATCAR
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py
```

## 输入规范
- `$AIMD_WORK_ROOT/<A>/AIMD/XDATCAR`
- 同目录 `INCAR` 含 `POTIM`（fs）；或显式 `--dt`
- 体系阶段目录：`opt` / `scf-MD` / `AIMD`

## 输出
- `$AIMD_WORK_ROOT/MSD_data_for_origin/<A>_msd_data.dat`
- `$AIMD_WORK_ROOT/MSD_png/<A>_msd_rmsd.png`

## 依赖
```bash
pip install numpy matplotlib
```

## 注意事项
- 空 `AIMD_SCRIPTS_ROOT` 会导致错误绝对路径（先 `source deploy.env`）
- 批量默认不出图（`--with-plot`）
- 算法与旧 flex 一致；变更主要在路径 / dt / 汇总 mv
