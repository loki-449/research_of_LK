# VASP 工作流脚本使用说明（回答范式）

> 本文档位于 `calculation/`，是 VASP 模块的**统一参考**。  
> 说明所有脚本怎么用、生成什么、写到哪里，以及脚本之间的调用关系。  
> Agent / 人工回答 VASP 使用问题时，优先按本文档结构组织回答。  
>  
> **上手请先读主目录 [`VASP_QUICKSTART.md`](VASP_QUICKSTART.md)**（MVP → 高通量 → 分脚本）。  
> **新建/重构脚本前**：先走根 [`README.md`](README.md) 强制四步，并按 [`SCRIPT_DEPLOY_PARADIGM.md`](SCRIPT_DEPLOY_PARADIGM.md) 填规格。  
> 本文档本身是该范式在 VASP 上的**完整样例**。

---

## 0. 三类路径（必须先分清）

整个项目里出现 **三个不同概念**，名字里都有 `scf_ELF` 或 `opt`，切勿混淆：

| 名称 | 典型路径 | 性质 | 何时存在 | 能否删除 |
|------|----------|------|----------|----------|
| **A. 仓库遗留空目录** | `calculation/vasp/scf_ELF/` | 重构前的脚本目录残留，**当前为空** | 历史遗留 | **✅ 应删除**（逻辑中完全不使用） |
| **B. 脚本包目录** | `calculation/vasp/scripts/scf_ELF/` | ELF 阶段的 **Python 入口脚本** | 仓库内常驻 | **❌ 不可删** |
| **C. 计算数据目录** | `$VASP_WORK_ROOT/<材料>/<压强>/scf_ELF/` | VASP ELF 计算的**输入/输出** | opt 完成后由脚本创建 | 运行时自动生成，**不是仓库文件** |

同理，`opt` 也有两种含义：

| 名称 | 典型路径 | 性质 |
|------|----------|------|
| **脚本包** | `vasp/scripts/opt/` | 结构优化入口脚本（仓库内） |
| **计算数据** | `$VASP_WORK_ROOT/<材料>/<压强>/opt/` | 结构优化输入/输出（运行时） |

**结论（关于删除）：**

- `vasp/scf_ELF/`（A）：**可以删**，工作流从头到尾不读不写这个路径。
- `vasp/scripts/scf_ELF/`（B）：**不能删**，`scf_contcar_to_poscar_ELF.py` 等脚本在这里。
- `$VASP_WORK_ROOT/.../scf_ELF/`（C）：**不能删**（若已有计算数据），是 ELF 计算的工作目录。

---

## 1. scf_ELF 功能说明（决策参考）

### 1.1 在工作流中的位置

```
QE relax.in
    ↓  [opt 阶段]  scripts/opt/*
$VASP_WORK_ROOT/<A>/<B>/opt/     ← 结构优化 (ISIF=3)
    ↓  VASP 产出 CONTCAR
    ↓  [scf_ELF 阶段]  scripts/scf_ELF/*
$VASP_WORK_ROOT/<A>/<B>/scf_ELF/ ← SCF + ELF (LELF=TRUE)
    ↓  VASP 产出 ELFCAR 等
```

**scf_ELF 阶段在 opt 之后**，不在流程开始时使用。  
开始时只需要 QE 输入；`scf_ELF/` 数据目录在 **opt 的 CONTCAR 就绪后** 才需要。

### 1.2 scf_ELF 阶段做什么

| 步骤 | 脚本 | 作用 |
|------|------|------|
| 主路径 | `scf_contcar_to_poscar_ELF.py` | 把 `opt/CONTCAR` 复制为 `scf_ELF/POSCAR`，可选写 `ELF.pbs` |
| 旁路 | `run_scf_batch.py` | 跳过 opt，直接从 QE `relax.in` 部署 scf_ELF（少用） |
| 后处理 | `remove_xcursor.py` | 清理 ELFCAR 目录里的 `xcursor.png` 垃圾文件 |

### 1.3 `scripts/scf_ELF/` 内各文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `scf_contcar_to_poscar_ELF.py` | **入口脚本** | 主流程，opt → scf_ELF 结构传递 |
| `run_scf_batch.py` | **入口脚本** | 从 QE 一键部署 scf_ELF |
| `elf_common.py` | 兼容层 | 旧代码 import 用，新流程不必直接调用 |
| `remove_xcursor.py` | 工具 | 与部署无关的后处理 |

公共逻辑在 `scripts/lib/scf_common.py`（写 `ELF.pbs`、LELF INCAR 等）。

---

## 2. 环境与路径变量

使用前加载配置（见 `vasp/deploy.env.example`）：

```bash
source /path/to/vasp/deploy.env
```

| 变量 | 含义 | 示例值 |
|------|------|--------|
| `VASP_SCRIPTS_ROOT` | 脚本安装根 | `/home/test1/hhy/tools/vasp/scripts` |
| `VASP_WORK_ROOT` | **计算数据根** | `/home/test1/hhy/calculation/vasp_work` |
| `QE_ROOT` | QE 输入根 | `/home/test1/hhy/calculation/QE` |
| `PBE_LIB` | 赝势库 | `/home/test1/hhy/basic/psudopotential/PAW-GGA-PBE` |
| `VASP_PYTHON` | Python | `python3` |

工作根解析优先级：`--work-root` > `$VASP_WORK_ROOT` > 当前 `cd` 目录。

### 2.1 体系命名与目录映射

QE 文件夹名：`Ag-H-50GPa-300K`

| 解析字段 | 值 | 写入路径 |
|----------|-----|----------|
| 材料 A | `Ag` | |
| 压强 B | `50` | |
| 温度 C | `300` | 仅解析，不参与路径 |

**体系基目录：** `$VASP_WORK_ROOT/Ag/50/`  
**opt 工作目录：** `$VASP_WORK_ROOT/Ag/50/opt/`  
**scf_ELF 工作目录：** `$VASP_WORK_ROOT/Ag/50/scf_ELF/`

---

## 3. 全部脚本说明（用法 · 生成物 · 路径）

以下 `$WR` = `$VASP_WORK_ROOT`，`$SCR` = `$VASP_SCRIPTS_ROOT`，`$QE` = `$QE_ROOT`。  
示例体系：`Ag/50`（来自 `Ag-H-50GPa-300K`）。

---

### 3.1 lib/ — 公共库（不直接运行）

#### `bootstrap.py`

| 项目 | 内容 |
|------|------|
| 调用方式 | 被各入口脚本自动 `init_imports()` |
| 生成物 | 无 |
| 作用 | 加载 `deploy.env`；把 `lib/`、`opt/`、`scf_ELF/` 加入 `sys.path` |

#### `path_config.py`

| 项目 | 内容 |
|------|------|
| 调用方式 | 被入口脚本 import |
| 生成物 | 无 |
| 作用 | 解析 `work_root`、`scripts_root`；提供 `--work-root` 参数 |

#### `vasp_common.py`

| 项目 | 内容 |
|------|------|
| 调用方式 | 被 opt / scf 脚本 import |
| 生成物 | 无（提供写入函数） |
| 核心能力 | 解析 QE 命名、`relax.in` → POSCAR、POTCAR 拼接、写 PBS、管理 `opt/` 目录 |

**被以下函数写入 opt 目录：**

| 函数 | 写入路径 |
|------|----------|
| `setup_opt_scripts(base)` | `$WR/<A>/<B>/opt/opt.pbs` |
| `deploy_poscar_to_opt(...)` | `$WR/<A>/<B>/opt/POSCAR` |
| `deploy_potcar_to_opt(...)` | `$WR/<A>/<B>/opt/POTCAR` |
| `deploy_opt_system(relax_in, base)` | 以上三者 |

#### `scf_common.py`

| 项目 | 内容 |
|------|------|
| 调用方式 | 被 scf_ELF 脚本 import |
| 生成物 | 无（提供写入函数） |
| 核心能力 | LELF=TRUE INCAR、`scf_ELF/` 目录管理 |

**被以下函数写入 scf_ELF 目录：**

| 函数 | 写入路径 |
|------|----------|
| `setup_scf_scripts(base)` | `$WR/<A>/<B>/scf_ELF/ELF.pbs` |
| `deploy_poscar_to_scf(...)` | `$WR/<A>/<B>/scf_ELF/POSCAR` |
| `deploy_potcar_to_scf(...)` | `$WR/<A>/<B>/scf_ELF/POTCAR` |
| `deploy_scf_system(relax_in, base)` | 以上三者 |

---

### 3.2 opt/ — 结构优化入口脚本

#### `setup_opt_workflow.py`

| 项目 | 内容 |
|------|------|
| **用途** | 扫描 QE 目录，建立 opt 目录并写 `opt.pbs` |
| **命令** | `$VASP_PYTHON $SCR/opt/setup_opt_workflow.py $QE` |
| **输入** | `$QE/*GPa*/relax.in`（默认 pattern `*GPa*`） |
| **生成物** | `opt.pbs` |
| **生成路径** | `$WR/<A>/<B>/opt/opt.pbs` |
| **可选** | `--with-poscar` 同时写 POSCAR；`--dry-run` 只打印 |
| **依赖库** | `vasp_common.setup_opt_scripts`；可选 `make_poscar.make_poscar_for_base` |
| **不生成** | POTCAR、CONTCAR、`.pbs_submitted` |

#### `make_poscar.py`

| 项目 | 内容 |
|------|------|
| **用途** | 从 QE `relax.in` 生成 VASP POSCAR |
| **命令（批量）** | `$VASP_PYTHON $SCR/opt/make_poscar.py --scan $QE` |
| **命令（单个）** | `$VASP_PYTHON $SCR/opt/make_poscar.py $QE/Ag-H-50GPa-300K` |
| **命令（手动）** | `--relax-in PATH --base-dir $WR/Ag/50` |
| **输入** | QE 体系目录或 `relax.in` |
| **生成物** | `POSCAR` |
| **生成路径** | `$WR/<A>/<B>/opt/POSCAR` |
| **依赖库** | `vasp_common.deploy_poscar_to_opt` |
| **说明** | 默认不覆盖已有 `opt.pbs`；`--write-pbs` 可重写 PBS |

#### `make_potcar.py`

| 项目 | 内容 |
|------|------|
| **用途** | 按 POSCAR 元素顺序拼接 POTCAR |
| **命令（批量）** | `$VASP_PYTHON $SCR/opt/make_potcar.py --scan $WR` |
| **命令（单个）** | `--poscar $WR/Ag/50/opt/POSCAR -o $WR/Ag/50/opt/POTCAR` |
| **输入** | 已有 `opt/POSCAR`；赝势库 `$PBE_LIB` |
| **生成物** | `POTCAR` |
| **生成路径** | `$WR/<A>/<B>/opt/POTCAR` |
| **依赖库** | `vasp_common.assemble_potcar` |
| **择优规则** | ZVAL 最大 → 日期最新 |

#### `run_opt_batch.py`

| 项目 | 内容 |
|------|------|
| **用途** | 一键完成 setup + POSCAR + POTCAR |
| **命令** | `$VASP_PYTHON $SCR/opt/run_opt_batch.py $QE` |
| **输入** | `$QE/*GPa*/relax.in` |
| **生成物** | `opt.pbs` + `POSCAR` + `POTCAR` |
| **生成路径** | `$WR/<A>/<B>/opt/` 下上述三文件 |
| **依赖库** | `vasp_common.deploy_opt_system` |
| **等价于** | `setup_opt_workflow` + `make_poscar` + `make_potcar`（逐步合并） |
| **可选** | `--skip-existing` 已有 POSCAR+POTCAR 则跳过 |

#### `submit_opt.py`

| 项目 | 内容 |
|------|------|
| **用途** | 批量 `qsub opt.pbs` |
| **命令** | `$VASP_PYTHON $SCR/opt/submit_opt.py` 或 `$WR` |
| **输入** | `$WR/*/*/opt/opt.pbs`（通过 `iter_opt_work_dirs` 扫描） |
| **生成物** | `.pbs_submitted`（提交标记） |
| **生成路径** | `$WR/<A>/<B>/opt/.pbs_submitted` |
| **VASP 运行后** | `$WR/<A>/<B>/opt/CONTCAR`（**非本脚本生成**，VASP 产出） |
| **依赖库** | `vasp_common.iter_opt_work_dirs` |
| **可选** | `--resubmit` `--max-jobs N` `--dry-run` `--clear-markers` |

---

### 3.3 scf_ELF/ — ELF 计算入口脚本

#### `scf_contcar_to_poscar_ELF.py`（主流程）

| 项目 | 内容 |
|------|------|
| **用途** | opt 完成后，CONTCAR → scf_ELF/POSCAR |
| **命令（批量）** | `$VASP_PYTHON $SCR/scf_ELF/scf_contcar_to_poscar_ELF.py --scan --write-pbs` |
| **命令（单体系）** | `--system-dir $WR/Ag/50 --write-pbs` |
| **输入** | `$WR/<A>/<B>/opt/CONTCAR`（**必须 opt 已算完**） |
| **生成物** | `POSCAR`；可选 `ELF.pbs` |
| **生成路径** | `$WR/<A>/<B>/scf_ELF/POSCAR`，`$WR/<A>/<B>/scf_ELF/ELF.pbs` |
| **依赖库** | `vasp_common.iter_opt_input_files`；`scf_common.setup_scf_scripts` |
| **不自动生成** | POTCAR（需手动从 opt 复制或另跑 `run_scf_batch`） |
| **VASP 运行后** | `ELFCAR`、`CHGCAR` 等 |

#### `run_scf_batch.py`（旁路）

| 项目 | 内容 |
|------|------|
| **用途** | 从 QE 直接部署 scf_ELF（不读 CONTCAR） |
| **命令** | `$VASP_PYTHON $SCR/scf_ELF/run_scf_batch.py $QE` |
| **输入** | `$QE/*GPa*/relax.in` |
| **生成物** | `ELF.pbs` + `POSCAR` + `POTCAR` |
| **生成路径** | `$WR/<A>/<B>/scf_ELF/` 下上述三文件 |
| **依赖库** | `scf_common.deploy_scf_system` |
| **与主路径关系** | **替代** `scf_contcar_to_poscar_ELF`；用 QE 初始结构而非 opt 优化结构 |

#### `elf_common.py`

| 项目 | 内容 |
|------|------|
| **用途** | 向后兼容 import 包装 |
| **生成物** | 无 |
| **说明** | 新流程不必直接运行 |

#### `remove_xcursor.py`

| 项目 | 内容 |
|------|------|
| **用途** | 删除 ELF 目录树中的 `xcursor.png` |
| **命令** | `python remove_xcursor.py $WR` |
| **生成物** | 无（删除文件） |
| **说明** | 与 opt/scf 部署链无关，算完后可选清理 |

---

## 4. 脚本关联图

```
                    ┌─────────────────────────────────────────┐
                    │           QE_ROOT                        │
                    │  Ag-H-50GPa-300K/relax.in               │
                    └─────────────────┬───────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │ opt 阶段                   │                            │ scf 旁路
         ▼                            │                            ▼
 setup_opt_workflow.py ──→ opt.pbs    │              run_scf_batch.py
 make_poscar.py ─────────→ POSCAR     │                    │
 make_potcar.py ──────────→ POTCAR     │                    ▼
         │         ╲                   │         scf_ELF/{ELF.pbs,POSCAR,POTCAR}
 run_opt_batch.py ════════╧═ 以上三步合一
         │
         ▼
 submit_opt.py ──→ qsub ──→ VASP(opt) ──→ CONTCAR
         │                                      │
         │                                      ▼
         │                    scf_contcar_to_poscar_ELF.py
         │                              │
         │                              ▼
         │                    scf_ELF/{POSCAR, ELF.pbs}
         │                              │
         │                         (补 POTCAR)
         │                              │
         │                              ▼
         │                         qsub ELF.pbs ──→ ELFCAR
         │
         └── 依赖 lib/vasp_common.py

 scf 阶段依赖 lib/scf_common.py + lib/vasp_common.py
 所有入口脚本启动 → lib/bootstrap.py → lib/path_config.py
```

### 4.1 调用关系表

| 入口脚本 | 直接 import / 调用 |
|----------|-------------------|
| `setup_opt_workflow.py` | `vasp_common`；可选 `make_poscar.make_poscar_for_base` |
| `make_poscar.py` | `vasp_common` |
| `make_potcar.py` | `vasp_common` |
| `run_opt_batch.py` | `vasp_common.deploy_opt_system` |
| `submit_opt.py` | `vasp_common.iter_opt_work_dirs` |
| `scf_contcar_to_poscar_ELF.py` | `vasp_common.iter_opt_input_files`；`scf_common.setup_scf_scripts` |
| `run_scf_batch.py` | `scf_common.deploy_scf_system` → `vasp_common` |

### 4.2 数据依赖链

```
relax.in ──→ [opt 脚本] ──→ opt/{opt.pbs,POSCAR,POTCAR}
                                    │
                              submit_opt + VASP
                                    │
                                    ▼
                              opt/CONTCAR
                                    │
                    scf_contcar_to_poscar_ELF.py
                                    │
                                    ▼
                         scf_ELF/{POSCAR,ELF.pbs,POTCAR?}
                                    │
                              qsub + VASP
                                    │
                                    ▼
                              scf_ELF/ELFCAR
```

---

## 5. 标准使用流程

### 5.1 分步（推荐）

```bash
source deploy.env
PY=$VASP_PYTHON; SCR=$VASP_SCRIPTS_ROOT

# ── opt ──
$PY $SCR/opt/setup_opt_workflow.py $QE_ROOT
$PY $SCR/opt/make_poscar.py --scan $QE_ROOT
$PY $SCR/opt/make_potcar.py --scan $VASP_WORK_ROOT
$PY $SCR/opt/submit_opt.py
# 等待 CONTCAR

# ── scf_ELF ──
$PY $SCR/scf_ELF/scf_contcar_to_poscar_ELF.py --scan --write-pbs
cp $VASP_WORK_ROOT/Ag/50/opt/POTCAR $VASP_WORK_ROOT/Ag/50/scf_ELF/   # 元素不变时
cd $VASP_WORK_ROOT/Ag/50/scf_ELF && qsub ELF.pbs
```

### 5.2 一键 opt

```bash
$PY $SCR/opt/run_opt_batch.py $QE_ROOT
$PY $SCR/opt/submit_opt.py
```

---

## 6. 各阶段目录产物对照表

### `$WR/Ag/50/opt/`（opt 阶段）

| 文件 | 谁生成 | 何时出现 |
|------|--------|----------|
| `opt.pbs` | setup / run_opt_batch | 部署时 |
| `POSCAR` | make_poscar / run_opt_batch | 部署时 |
| `POTCAR` | make_potcar / run_opt_batch | 部署时 |
| `.pbs_submitted` | submit_opt | 提交后 |
| `CONTCAR` | **VASP** | opt 算完后 |
| `log` 等 | **VASP** | 运行时 |

### `$WR/Ag/50/scf_ELF/`（scf_ELF 阶段）

| 文件 | 谁生成 | 何时出现 |
|------|--------|----------|
| `POSCAR` | scf_contcar（从 CONTCAR 复制）或 run_scf_batch | scf 部署时 |
| `ELF.pbs` | scf_contcar `--write-pbs` 或 run_scf_batch | scf 部署时 |
| `POTCAR` | run_scf_batch；或手动从 opt 复制 | scf 部署时 |
| `ELFCAR` | **VASP** | ELF 算完后 |
| `CHGCAR` | **VASP** | 运行时 |

---

## 7. 回答范式（Agent / 人工复用模板）

回答 VASP 使用类问题时，按以下结构组织：

---

**【路径说明】**  
- 脚本在：`$VASP_SCRIPTS_ROOT`（仓库内 `vasp/scripts/`）  
- 数据在：`$VASP_WORK_ROOT/<材料>/<压强>/opt|scf_ELF/`  
- `vasp/scf_ELF/` 空目录可删；`scripts/scf_ELF/` 不可删  

**【当前阶段】** opt / scf_ELF / 全流程  

**【推荐命令】**（列出具体命令，带 `$QE_ROOT`、`$VASP_WORK_ROOT`）  

**【本步生成物】**

| 文件 | 路径 |
|------|------|
| ... | `$WR/Ag/50/opt/...` |

**【下一步】** 上一步产物 → 下一步脚本 → 下一步产物  

**【前置条件】** 例如 scf 需要 `opt/CONTCAR` 已存在  

**【关联脚本】** 本脚本等价于 / 依赖 / 被谁调用  

---

### 示例：用户问「opt 脚本怎么用」

**【路径说明】**  
脚本位于 `vasp/scripts/opt/`；输出写入 `$VASP_WORK_ROOT/<A>/<B>/opt/`。

**【当前阶段】** opt 结构优化部署

**【推荐命令】**
```bash
source deploy.env
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/setup_opt_workflow.py $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_poscar.py --scan $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_potcar.py --scan $VASP_WORK_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py
```

**【本步生成物】**

| 文件 | 路径 | 生成脚本 |
|------|------|----------|
| opt.pbs | `$WR/Ag/50/opt/opt.pbs` | setup_opt_workflow |
| POSCAR | `$WR/Ag/50/opt/POSCAR` | make_poscar |
| POTCAR | `$WR/Ag/50/opt/POTCAR` | make_potcar |
| .pbs_submitted | `$WR/Ag/50/opt/.pbs_submitted` | submit_opt |
| CONTCAR | `$WR/Ag/50/opt/CONTCAR` | VASP（算完后） |

**【下一步】** CONTCAR 就绪后 → `scripts/scf_ELF/scf_contcar_to_poscar_ELF.py --scan --write-pbs`

**【前置条件】** QE 目录命名符合 `*-GPa-*K`，且含 `relax.in`

**【关联脚本】** `run_opt_batch.py` = 前三步合并；`submit_opt.py` 独立提交

---

### 示例：用户问「scf_ELF 文件夹要不要删」

**【路径说明】** 先确认用户指的是哪一个：

| 路径 | 建议 |
|------|------|
| `vasp/scf_ELF/`（仓库根下空目录） | **删** |
| `vasp/scripts/scf_ELF/` | **保留**（脚本） |
| `$VASP_WORK_ROOT/.../scf_ELF/` | **保留**（计算数据） |

**【功能说明】** scf_ELF 阶段在 opt 之后，读取 `opt/CONTCAR`，写入 `scf_ELF/POSCAR` 和 `ELF.pbs`，用于 LELF=TRUE 的 ELF 计算。

**【当前阶段】** 不属于流程开始；opt 完成 CONTCAR 后才需要。

---

## 8. 相关文件索引

| 文件 | 位置 |
|------|------|
| 强制工作流（四步） | `README.md` |
| **快速上手（MVP→高通量→分脚本）** | `VASP_QUICKSTART.md` |
| 脚本部署范式（规格/模板） | `SCRIPT_DEPLOY_PARADIGM.md` |
| Cursor 部署技能 | `.cursor/skills/calc-script-deploy/` |
| 部署配置模板 | `vasp/deploy.env.example` |
| 模块总 README | `vasp/README.md` |
| 脚本包 README | `vasp/scripts/README.md` |
| opt 详细说明 | `vasp/scripts/opt/README.md` |
| scf_ELF 详细说明 | `vasp/scripts/scf_ELF/README.md` |
| Agent 路由 | `vasp/CLAUDE.md` |

---

*文档版本：与 `vasp/scripts/` 当前结构一致。路径示例来自 `deploy.env.example`。*
