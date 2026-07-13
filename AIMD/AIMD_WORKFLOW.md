# AIMD 工作流（回答范式）

> **上手请先读主目录 [`AIMD_QUICKSTART.md`](../AIMD_QUICKSTART.md)**（MVP → 高通量 → 分脚本）。  
> 本文偏完整路径辨析与 Agent 回答模板。规格：[`AIMD_DEPLOY_SPEC.md`](AIMD_DEPLOY_SPEC.md)。  
> 旧路径 `MSD&RMSD/` 已迁移至 `scripts/MSD_RMSD/`。

---

## 0. 路径两类

| 名称 | 路径 | 说明 |
|------|------|------|
| 脚本包 | `$AIMD_SCRIPTS_ROOT` | `AIMD/scripts/` |
| 计算数据 | `$AIMD_WORK_ROOT/<A>/{opt,scf-MD,AIMD}/` | XDATCAR 在 `AIMD/` |
| 汇总 | `$AIMD_WORK_ROOT/MSD_data_for_origin/`、`MSD_png/` | extract/plot 默认 `mv` 写入 |

与 VASP 的 `VASP_*` **变量名分离**，勿混用。

---

## 1. 环境

```bash
source AIMD/deploy.env
```

| 变量 | 含义 |
|------|------|
| `AIMD_SCRIPTS_ROOT` | 脚本根 |
| `AIMD_WORK_ROOT` | 数据根 |
| `AIMD_PYTHON` | Python |
| `AIMD_DEPLOY_ENV` | 供 bootstrap 自动加载 |

**无静态 `AIMD_DT_DEFAULT`。** 每个体系从 `$WR/<A>/AIMD/INCAR` 读 **POTIM**（fs）。

### POTIM 与其它 INCAR 参数

| 参数 | 对 MSD 的影响 |
|------|----------------|
| **POTIM** | `Time(ps)=frame*POTIM/1000`；错读则时间轴与扩散斜率整体错 |
| NSW | 轨迹长度（帧数） |
| TEBEG/TEEND / 系综 | 影响物理轨迹，不改本公式 |
| `--dt` CLI | 覆盖 POTIM；不一致时 WARNING |

---

## 2. 脚本

| 脚本 | 输入 | 生成物 |
|------|------|--------|
| `extract_msd_flex.py` | `.../AIMD/XDATCAR` (+INCAR) | `<A>/msd_data.dat` → **mv** `MSD_data_for_origin/<A>_msd_data.dat` |
| `run_msd_batch.py` | `$WR/*/AIMD/XDATCAR` | 同上批量；默认无 png |
| `plot_msd_flex.py` | 汇总 .dat | → **mv** `MSD_png/<A>_msd_rmsd.png` |
| `xdatcar_msd_flex.py` | XDATCAR | 摘要；可选 dat/png + publish |
| `compat/*` | — | Deprecated |

---

## 3. 标准流程

```bash
source deploy.env
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py
# 出图
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py --with-plot
```

---

## 4. 回答范式

```
【路径说明】SCR=… WR=…；汇总在 MSD_data_for_origin / MSD_png
【当前阶段】MSD 提取 / 绘图
【推荐命令】…
【本步生成物】表
【前置条件】<A>/AIMD/XDATCAR + INCAR(POTIM)
【下一步】…
```

---

## 5. 简易卡

```bash
source deploy.env
echo SCR=[$AIMD_SCRIPTS_ROOT] WR=[$AIMD_WORK_ROOT]
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py \
  $AIMD_WORK_ROOT/<A>/AIMD/XDATCAR
ls $AIMD_WORK_ROOT/MSD_data_for_origin/
```
