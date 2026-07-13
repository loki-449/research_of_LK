# AIMD 快速上手（MVP → 高通量 → 分脚本）

> **主目录范式文档**：本文件是 `SCRIPT_DEPLOY_PARADIGM.md` 要求的「简易卡 + 分层流程」在 AIMD 上的**落地样例**。  
> 详细规格 / 回答范式见 [`AIMD/AIMD_WORKFLOW.md`](AIMD/AIMD_WORKFLOW.md)、[`AIMD/AIMD_DEPLOY_SPEC.md`](AIMD/AIMD_DEPLOY_SPEC.md)。  
> **阅读顺序**：① 本页 MVP → ② 高通量 → ③ 分脚本；需要改代码时再读规格与 WORKFLOW。

---

## 0. 30 秒概念

| 概念 | 是什么 |
|------|--------|
| 脚本在哪 | `$AIMD_SCRIPTS_ROOT` ← `AIMD/scripts/` |
| 数据在哪 | `$AIMD_WORK_ROOT/<A>/{opt,scf-MD,AIMD}/` |
| 算什么 | 读 `<A>/AIMD/XDATCAR`，算 MSD/RMSD |
| dt 从哪来 | 同目录 `INCAR` 的 **POTIM**（fs），不是写死 1.0 |
| 结果去哪 | `mv` → `$AIMD_WORK_ROOT/MSD_data_for_origin/<A>_msd_data.dat`；图 → `MSD_png/<A>_msd_rmsd.png` |

```
$AIMD_WORK_ROOT/
├── MSD_data_for_origin/     # 汇总 .dat
├── MSD_png/                 # 汇总 png
└── <A>/
    ├── opt/  scf-MD/        # 本模块 MSD 不读
    └── AIMD/
        ├── XDATCAR          # ★ 必须
        └── INCAR            # ★ 含 POTIM=
```

---

## 1. MVP 计算流程（最先跑通）

**目标**：1 个体系、少量帧、确认路径与 POTIM 正确。  
**仓库已备样例**：`AIMD/example/Step3_Production_with_H/`（裁剪帧 + INCAR）。

### 1.1 一次性环境

```bash
cd calculation/AIMD
cp deploy.env.example deploy.env
# 编辑：AIMD_SCRIPTS_ROOT、AIMD_WORK_ROOT、AIMD_DEPLOY_ENV
# 本地 MVP 可直接：
#   AIMD_SCRIPTS_ROOT=<仓库>/AIMD/scripts
#   AIMD_WORK_ROOT=<仓库>/AIMD/example

source deploy.env
echo "SCR=[$AIMD_SCRIPTS_ROOT] WR=[$AIMD_WORK_ROOT]"   # 必须非空
pip install numpy matplotlib
```

### 1.2 一条命令提取

```bash
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py \
  $AIMD_WORK_ROOT/Step3_Production_with_H/AIMD/XDATCAR
```

**成功标志**

| 检查 | 期望 |
|------|------|
| 终端 | 打印 `dt: 0.5 fs (INCAR POTIM=...)`（样例为 0.5） |
| 文件 | `$AIMD_WORK_ROOT/MSD_data_for_origin/Step3_Production_with_H_msd_data.dat` |
| 内容 | 有表头 `Time(ps)`、`H_MSD` / `Ag_MSD` / `Ba_MSD` 等 |

### 1.3（可选）出图

```bash
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/plot_msd_flex.py \
  --work-root $AIMD_WORK_ROOT \
  --system-dir $AIMD_WORK_ROOT/Step3_Production_with_H
# → MSD_png/Step3_Production_with_H_msd_rmsd.png
```

### 1.4 MVP 故障 3 条

| 现象 | 处理 |
|------|------|
| `python ... /MSD_RMSD/...` 找不到 | `AIMD_SCRIPTS_ROOT` 空 → 先 `source deploy.env` |
| `POTIM not found` | 在 `<A>/AIMD/INCAR` 写 `POTIM = ...` 或加 `--dt` |
| 无 `.dat` | 确认路径是 `.../<A>/AIMD/XDATCAR` |

---

## 2. 高通量计算流程

**前提**：多个体系已按 `$WR/<A>/AIMD/{XDATCAR,INCAR}` 放好。

```bash
source /path/to/AIMD/deploy.env

# 批量提取（默认不出图；各体系自读 POTIM）
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py

# 已有汇总 dat 则跳过
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py --skip-existing

# 提取 + 出图
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py --with-plot

# 只看计划
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py --dry-run
```

**扫描规则**：`$AIMD_WORK_ROOT/*/AIMD/XDATCAR`（自动跳过 `MSD_data_for_origin`、`MSD_png`）。

**每体系产物**

| 中间（默认被 mv 走） | 汇总 |
|----------------------|------|
| `$WR/<A>/msd_data.dat` | `$WR/MSD_data_for_origin/<A>_msd_data.dat` |
| （`--with-plot`）临时 png | `$WR/MSD_png/<A>_msd_rmsd.png` |

**常用覆盖参数**（整批统一时才用）：`--dt`、`--stride`、`--elements H Ag`、`--keep-local`（汇总后仍留体系下副本）。

---

## 3. 分脚本单独运行流程

以下均先：`source deploy.env`。`$A` = 体系名，`$X` = `$AIMD_WORK_ROOT/$A/AIMD/XDATCAR`。

### 3.1 `extract_msd_flex.py` — 提取

```bash
# 单体系（推荐）
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py $X

# 自带批量（等价 run_msd_batch 的提取部分）
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py --scan --work-root $AIMD_WORK_ROOT

# 显式 dt / 保留本地 / 不 mv 汇总
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py $X --dt 0.5 --keep-local
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py $X --no-publish -o ./out.dat
```

| 项 | 内容 |
|----|------|
| 输入 | XDATCAR；默认读同级 `INCAR`→POTIM |
| 生成 | `<A>/msd_data.dat` →（默认）汇总目录 |
| 不生成 | png |

### 3.2 `run_msd_batch.py` — 高通量入口

```bash
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py --with-plot --skip-existing
```

| 项 | 内容 |
|----|------|
| 输入 | `$WR/*/AIMD/XDATCAR` |
| 生成 | 各体系汇总 `.dat`；（可选）png |
| 默认 | **不出图** |

### 3.3 `plot_msd_flex.py` — 只出图

```bash
# 从汇总 .dat 出图并 mv 到 MSD_png
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/plot_msd_flex.py \
  --work-root $AIMD_WORK_ROOT \
  --system-dir $AIMD_WORK_ROOT/$A

# 直接指定文件
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/plot_msd_flex.py \
  $AIMD_WORK_ROOT/MSD_data_for_origin/${A}_msd_data.dat \
  --no-publish -o ./preview.png
```

| 项 | 内容 |
|----|------|
| 输入 | 汇总 `<A>_msd_data.dat`（或未 mv 的 `<A>/msd_data.dat`） |
| 生成 | `MSD_png/<A>_msd_rmsd.png` |
| 依赖 | `matplotlib` |

### 3.4 `xdatcar_msd_flex.py` — 一键摘要(+图)

```bash
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/xdatcar_msd_flex.py $X --no-plot
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/xdatcar_msd_flex.py $X --write-dat
```

| 项 | 内容 |
|----|------|
| 输入 | XDATCAR + INCAR |
| 生成 | 终端摘要；默认可出图并 publish；`--write-dat` 才写/汇总 `.dat` |

### 3.5 `plot_line_template.py` — 通用折线

```bash
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/plot_line_template.py \
  $AIMD_WORK_ROOT/MSD_data_for_origin/${A}_msd_data.dat -o custom.png
```

改脚本顶部「配置区」可换列/样式；非 MSD 表也能用。

### 3.6 `compat/*` — 不要用（除非旧流程）

已 Deprecated，见 `AIMD/scripts/compat/README.md`。新流程只用 `MSD_RMSD/`。

---

## 4. 脚本信息速查表

| 脚本 | 一句话 | 典型命令动词 |
|------|--------|--------------|
| `extract_msd_flex.py` | XDATCAR→dat→汇总 | 单体系 / `--scan` |
| `run_msd_batch.py` | 批量 extract（±图） | 日常高通量 |
| `plot_msd_flex.py` | dat→双子图→MSD_png | 已有 dat 后出图 |
| `xdatcar_msd_flex.py` | 计算+摘要(+图) | 快速肉眼看趋势 |
| `plot_line_template.py` | 配置驱动折线 | 自定义样式 |
| `lib/msd_common.py` | 库：POTIM、mv、读轨迹 | 不直接跑 |

**INCAR 参数与结果（摘要）**

| 参数 | 影响 |
|------|------|
| **POTIM** | 时间轴 `Time(ps)=frame*POTIM/1000`；错则扩散斜率整体错 |
| NSW | 轨迹长度 |
| TEBEG/系综等 | 改物理轨迹，不改本脚本公式 |

---

## 5. 文档导航（主目录范式中的位置）

| 文档 | 何时打开 |
|------|----------|
| **本文件** `AIMD_QUICKSTART.md` | **上手 / 跑通 / 日常命令** |
| [`VASP_QUICKSTART.md`](VASP_QUICKSTART.md) | VASP 同构上手 |
| [`SCRIPT_DEPLOY_PARADIGM.md`](SCRIPT_DEPLOY_PARADIGM.md) | 新建模块时抄结构与手册分层 |
| [`AIMD/AIMD_WORKFLOW.md`](AIMD/AIMD_WORKFLOW.md) | 回答范式、完整路径辨析 |
| [`AIMD/AIMD_DEPLOY_SPEC.md`](AIMD/AIMD_DEPLOY_SPEC.md) | 规格表、产物约定溯源 |
| [`AIMD/scripts/MSD_RMSD/README.md`](AIMD/scripts/MSD_RMSD/README.md) | 阶段 README |
| [`VASP_WORKFLOW.md`](VASP_WORKFLOW.md) | VASP 同结构对照（非 AIMD 命令） |

---

*样例 POTIM=0.5 fs 来自 `test/INCAR` → `example/Step3_Production_with_H`。*
