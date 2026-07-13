# VASP 快速上手（MVP → 高通量 → 分脚本）

> **主目录范式文档**：与 [`AIMD_QUICKSTART.md`](AIMD_QUICKSTART.md) 同构；对应 `SCRIPT_DEPLOY_PARADIGM.md` §5.5。  
> 详细用法 / 生成物 / 回答范式见 [`VASP_WORKFLOW.md`](VASP_WORKFLOW.md)。  
> **阅读顺序**：① MVP → ② 高通量 → ③ 分脚本。

---

## 0. 30 秒概念

| 概念 | 是什么 |
|------|--------|
| 脚本在哪 | `$VASP_SCRIPTS_ROOT` ← `vasp/scripts/` |
| 数据在哪 | `$VASP_WORK_ROOT/<材料A>/<压强B>/opt/` 与 `scf_ELF/` |
| QE 输入 | `$QE_ROOT/*GPa*/relax.in`（命名如 `Ag-H-50GPa-300K`） |
| 赝势 | `$PBE_LIB`（POTCAR 择优：ZVAL 最大 → 日期最新） |
| 顺序 | **先 opt，再 scf_ELF**（主路径需要 `opt/CONTCAR`） |

```
$VASP_WORK_ROOT/
└── Ag/50/                    # A=材料, B=压强（温度不进路径）
    ├── opt/                  # opt.pbs, POSCAR, POTCAR → VASP → CONTCAR
    └── scf_ELF/              # POSCAR(←CONTCAR), ELF.pbs, POTCAR → ELFCAR
```

**三类路径勿混**：脚本包 `scripts/` ≠ 数据根 `$VASP_WORK_ROOT` ≠ 旧空目录（已删的 `vasp/scf_ELF/`）。

---

## 1. MVP 计算流程（最先跑通）

**目标**：1 个 QE 体系，只部署到写出 `opt/{opt.pbs,POSCAR,POTCAR}`，**先不强制 qsub**（无 PBS 亦可验路径）。

### 1.1 一次性环境

```bash
cd calculation/vasp
cp deploy.env.example deploy.env
# 编辑 VASP_SCRIPTS_ROOT / VASP_WORK_ROOT / QE_ROOT / PBE_LIB / VASP_DEPLOY_ENV

source deploy.env
echo "SCR=[$VASP_SCRIPTS_ROOT] WR=[$VASP_WORK_ROOT] QE=[$QE_ROOT]"
# 三者均须非空；SCR 空会出现 python3 /opt/xxx.py 报错
```

### 1.2 分步部署（推荐 MVP）

假定 QE 下已有一个体系目录（含 `relax.in`），例如 `Ag-H-50GPa-300K`：

```bash
# ① 建目录 + opt.pbs
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/setup_opt_workflow.py $QE_ROOT

# ② POSCAR
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_poscar.py --scan $QE_ROOT

# ③ POTCAR（依赖上一步 POSCAR + PBE_LIB）
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_potcar.py --scan $VASP_WORK_ROOT
```

**成功标志（以 Ag/50 为例）**

| 检查 | 期望 |
|------|------|
| 目录 | `$VASP_WORK_ROOT/Ag/50/opt/` |
| 文件 | `opt.pbs`、`POSCAR`、`POTCAR` 均非空 |
| 终端 | make_potcar 打印各元素 `ZVAL=...` |

### 1.3（可选）试提交

```bash
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py --dry-run
# 集群有 qsub 时再去掉 --dry-run
```

### 1.4 MVP 故障 3 条

| 现象 | 处理 |
|------|------|
| `can't open file '/opt/....py'` | `$VASP_SCRIPTS_ROOT` 空 → `source deploy.env` |
| 无体系被处理 | QE 目录名需匹配 `*GPa*` 且含 `relax.in` |
| `PBE library not found` / 缺元素 | 检查 `$PBE_LIB` 与元素 POTCAR |

---

## 2. 高通量计算流程

### 2.A opt 阶段（批量）

```bash
source /path/to/vasp/deploy.env

# 方式一：分步（易排查）
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/setup_opt_workflow.py $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_poscar.py --scan $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_potcar.py --scan $VASP_WORK_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py

# 方式二：一键部署输入（再提交）
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/run_opt_batch.py $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py --skip-existing   # 若用 run 的 skip：见下
```

`run_opt_batch.py` 可选：`--skip-existing`（已有 POSCAR+POTCAR 则跳过）、`--dry-run`。  
`submit_opt.py` 可选：`--dry-run`、`--resubmit`、`--max-jobs N`、`--clear-markers`。

**等待**：各 `$WR/<A>/<B>/opt/CONTCAR` 由 **VASP** 生成（非本仓库脚本写出）。

### 2.B scf_ELF 阶段（opt 完成后）

```bash
# CONTCAR → scf_ELF/POSCAR，并写 ELF.pbs
$VASP_PYTHON $VASP_SCRIPTS_ROOT/scf_ELF/scf_contcar_to_poscar_ELF.py --scan --write-pbs

# 元素不变时补 POTCAR（示例）
cp $VASP_WORK_ROOT/Ag/50/opt/POTCAR $VASP_WORK_ROOT/Ag/50/scf_ELF/

# 提交 ELF（集群）
cd $VASP_WORK_ROOT/Ag/50/scf_ELF && qsub ELF.pbs
```

**旁路**（跳过 opt、直接从 QE 部署 scf，少用）：

```bash
$VASP_PYTHON $VASP_SCRIPTS_ROOT/scf_ELF/run_scf_batch.py $QE_ROOT
```

---

## 3. 分脚本单独运行流程

以下均先：`source deploy.env`。`$WR=$VASP_WORK_ROOT`，`$QE=$QE_ROOT`，`$SCR=$VASP_SCRIPTS_ROOT`。

### 3.1 `setup_opt_workflow.py`

```bash
$VASP_PYTHON $SCR/opt/setup_opt_workflow.py $QE
$VASP_PYTHON $SCR/opt/setup_opt_workflow.py $QE --with-poscar --dry-run
```

| 项 | 内容 |
|----|------|
| 输入 | `$QE/*GPa*/relax.in` |
| 生成 | `$WR/<A>/<B>/opt/opt.pbs`；（`--with-poscar` 时）POSCAR |
| 不生成 | POTCAR、CONTCAR |

### 3.2 `make_poscar.py`

```bash
$VASP_PYTHON $SCR/opt/make_poscar.py --scan $QE
$VASP_PYTHON $SCR/opt/make_poscar.py $QE/Ag-H-50GPa-300K
$VASP_PYTHON $SCR/opt/make_poscar.py --relax-in PATH --base-dir $WR/Ag/50
```

| 项 | 内容 |
|----|------|
| 生成 | `$WR/<A>/<B>/opt/POSCAR` |
| 可选 | `--write-pbs` 重写 opt.pbs |

### 3.3 `make_potcar.py`

```bash
$VASP_PYTHON $SCR/opt/make_potcar.py --scan $WR
$VASP_PYTHON $SCR/opt/make_potcar.py --poscar $WR/Ag/50/opt/POSCAR -o $WR/Ag/50/opt/POTCAR
```

| 项 | 内容 |
|----|------|
| 输入 | 已有 `opt/POSCAR`；`$PBE_LIB` |
| 生成 | `$WR/<A>/<B>/opt/POTCAR` |

### 3.4 `run_opt_batch.py`

```bash
$VASP_PYTHON $SCR/opt/run_opt_batch.py $QE
$VASP_PYTHON $SCR/opt/run_opt_batch.py $QE --skip-existing --dry-run
```

| 项 | 内容 |
|----|------|
| 等价于 | setup + make_poscar + make_potcar |
| 生成 | `opt.pbs` + POSCAR + POTCAR |

### 3.5 `submit_opt.py`

```bash
$VASP_PYTHON $SCR/opt/submit_opt.py
$VASP_PYTHON $SCR/opt/submit_opt.py $WR --dry-run
$VASP_PYTHON $SCR/opt/submit_opt.py --resubmit --max-jobs 4
```

| 项 | 内容 |
|----|------|
| 输入 | `$WR/*/*/opt/opt.pbs` |
| 生成 | `.pbs_submitted`；CONTCAR 由 VASP 事后产生 |

### 3.6 `scf_contcar_to_poscar_ELF.py`（主路径）

```bash
$VASP_PYTHON $SCR/scf_ELF/scf_contcar_to_poscar_ELF.py --scan --write-pbs
$VASP_PYTHON $SCR/scf_ELF/scf_contcar_to_poscar_ELF.py --system-dir $WR/Ag/50 --write-pbs
```

| 项 | 内容 |
|----|------|
| 前置 | `$WR/<A>/<B>/opt/CONTCAR` 已存在 |
| 生成 | `scf_ELF/POSCAR`；可选 `ELF.pbs` |
| 不自动生成 | POTCAR（需 cp 或走 `run_scf_batch`） |

### 3.7 `run_scf_batch.py`（旁路）

```bash
$VASP_PYTHON $SCR/scf_ELF/run_scf_batch.py $QE
```

| 项 | 内容 |
|----|------|
| 输入 | QE `relax.in`（不读 CONTCAR） |
| 生成 | `scf_ELF/{ELF.pbs,POSCAR,POTCAR}` |

### 3.8 `remove_xcursor.py`

```bash
python $SCR/scf_ELF/remove_xcursor.py $WR
```

清理 ELF 树中的 `xcursor.png`；与部署链无关。

---

## 4. 脚本信息速查表

| 脚本 | 阶段 | 一句话 |
|------|------|--------|
| `setup_opt_workflow.py` | opt | 建目录 + opt.pbs |
| `make_poscar.py` | opt | relax.in → POSCAR |
| `make_potcar.py` | opt | 拼 POTCAR |
| `run_opt_batch.py` | opt | 上三者合一 |
| `submit_opt.py` | opt | 批量 qsub |
| `scf_contcar_to_poscar_ELF.py` | scf | CONTCAR → scf POSCAR |
| `run_scf_batch.py` | scf | QE → scf 三件套（旁路） |
| `lib/vasp_common.py` / `scf_common.py` | — | 公共库，不直接跑 |

**逻辑链（主路径）**

```
QE relax.in → opt/{pbs,POSCAR,POTCAR} → qsub → CONTCAR
    → scf_ELF/{POSCAR,ELF.pbs} + POTCAR → qsub → ELFCAR
```

---

## 5. 文档导航

| 文档 | 何时打开 |
|------|----------|
| **本文件** `VASP_QUICKSTART.md` | **上手 / 日常命令** |
| [`VASP_WORKFLOW.md`](VASP_WORKFLOW.md) | 全脚本生成物路径、回答范式 |
| [`vasp/README.md`](vasp/README.md) | 模块总览 |
| [`vasp/scripts/opt/README.md`](vasp/scripts/opt/README.md) | opt 阶段细节 |
| [`vasp/scripts/scf_ELF/README.md`](vasp/scripts/scf_ELF/README.md) | ELF 阶段细节 |
| [`SCRIPT_DEPLOY_PARADIGM.md`](SCRIPT_DEPLOY_PARADIGM.md) | 部署范式 / §5.5 上手三层 |
| [`AIMD_QUICKSTART.md`](AIMD_QUICKSTART.md) | AIMD 同构上手 |

---

## 6. 一页卡（可贴集群）

```bash
source /path/to/vasp/deploy.env
echo SCR=[$VASP_SCRIPTS_ROOT] WR=[$VASP_WORK_ROOT] QE=[$QE_ROOT]

$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/setup_opt_workflow.py $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_poscar.py --scan $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_potcar.py --scan $VASP_WORK_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py --dry-run   # 确认后再正式提交

# CONTCAR 就绪后：
$VASP_PYTHON $VASP_SCRIPTS_ROOT/scf_ELF/scf_contcar_to_poscar_ELF.py --scan --write-pbs
```
