# ELF 计算部署脚本说明

脚本路径：`vasp/ELF/` 与 `ELF/`

从 Quantum ESPRESSO（QE）结构优化结果出发，批量建立 VASP ELF（电子局域函数）计算所需的目录、POSCAR、POTCAR 与 PBS 提交脚本。

---

## 目录结构

```
calculation/
├── ELF.md                              ← 本文件
├── vasp/
│   └── ELF/
│       ├── vasp_common.py              ← 共享工具 + opt 相关（核心库）
│       ├── setup_elf_workflow.py       ← ① opt_ELF 目录与 PBS 建立
│       ├── make_poscar.py              ← ② POSCAR 生成（opt_ELF）
│       ├── make_potcar.py              ← ③ POTCAR 拼接（opt_ELF）
│       ├── run_elf_batch.py            ← 一键批量 opt_ELF
│       └── submit_opt_elf.py           ← ④ 批量提交 opt_ELF PBS 任务
└── ELF/
    ├── scf_common.py                   ← scf_ELF 相关（LELF=TRUE INCAR）
    ├── run_scf_batch.py                ← scf_ELF 一键批量部署
    ├── elf_common.py                   ← 向后兼容包装（导入 vasp_common + scf_common）
    ├── setup_elf.sh                    ← 原版一键脚本（保留）
    └── remove_xcursor.py               ← 清理 xcursor.png 工具
```

---

## 职责拆分

| 模块 | 位置 | 职责 |
|------|------|------|
| `vasp_common.py` | `vasp/ELF/` | 共享工具（QE 解析 / relax.in / POSCAR / POTCAR / PBS）+ opt_ELF 部署 |
| `scf_common.py` | `ELF/` | SCF + ELF 计算（LELF=TRUE INCAR），导入 vasp_common 的共享工具 |
| `elf_common.py` | `ELF/` | 向后兼容模块，`from vasp_common import *` + `from scf_common import SCF_INCAR` |

---

## 功能拆分

### vasp/ELF/（opt_ELF — 结构优化）

| 步骤 | 脚本 | 功能 |
|------|------|------|
| ① | `setup_elf_workflow.py` | 建立 `vasp/ELF/<A>/<B>/opt_ELF`，写入 `ELF.pbs` |
| ② | `make_poscar.py` | 从 `relax.in` 生成 `POSCAR`（写入 opt_ELF） |
| ③ | `make_potcar.py` | 拼接 `POTCAR`（写入 opt_ELF） |
| 全流程 | `run_elf_batch.py` | 依次执行 ①②③ |
| ④ | `submit_opt_elf.py` | 批量提交 `opt_ELF/ELF.pbs`（防重复 + 队列限制） |

### ELF/（scf_ELF — ELF 计算）

| 步骤 | 脚本 | 功能 |
|------|------|------|
| scf | `run_scf_batch.py` | 建立 `ELF/<A>/<B>/scf_ELF`，写入 PBS + POSCAR + POTCAR |

---

## QE 文件夹命名约定

脚本默认扫描 QE 根目录下匹配 `*GPa*` 的子文件夹，并从文件夹名解析：

| 字段 | 规则 | 示例 `Ag-H-50GPa-300K` |
|------|------|------------------------|
| 材料 (A) | 第一个 `-` 之前 | `Ag` |
| 压强 (B) | 中间段第一个数字 | `50` |
| 温度 (C) | 末尾 `K` 前的数字 | `300` |

生成的目录结构：

```
vasp/ELF/Ag/50/
└── opt_ELF/     # VASP 结构优化（由 vasp/ELF 脚本管理）

ELF/Ag/50/
└── scf_ELF/     # VASP SCF + ELF 计算（由 ELF/ 脚本管理）
```

---

## 快速开始

### 方式 A：一键批量（最简单）

```bash
# opt_ELF 一键部署
cd vasp/ELF
python run_elf_batch.py /path/to/QE_folder

# scf_ELF 一键部署
cd ELF
python run_scf_batch.py /path/to/QE_folder
```

### 方式 B：分步执行（推荐）

```bash
# === opt_ELF（结构优化）===
cd vasp/ELF

# 步骤 1：建立 opt_ELF + ELF.pbs
python setup_elf_workflow.py /path/to/QE_folder

# 步骤 2：批量生成 POSCAR
python make_poscar.py --scan /path/to/QE_folder --elf-root ./vasp/ELF

# 或一步完成前两步：
python setup_elf_workflow.py /path/to/QE_folder --with-poscar

# 步骤 3：批量拼接 POTCAR
python make_potcar.py --scan ./vasp/ELF

# 步骤 4：批量提交 opt_ELF 任务
python submit_opt_elf.py ./vasp/ELF

# === scf_ELF（ELF 计算）===
cd ELF

# scf_ELF 一键建立
python run_scf_batch.py /path/to/QE_folder --elf-root ./ELF
```

### 方式 C：单个体系手动处理

```bash
cd vasp/ELF

python setup_elf_workflow.py /path/to/QE_folder
python make_poscar.py /path/to/QE_folder/Ag-H-50GPa-300K --elf-root ./vasp/ELF
python make_potcar.py --poscar vasp/ELF/Ag/50/opt_ELF/POSCAR -o vasp/ELF/Ag/50/opt_ELF/POTCAR
```

---

## 各脚本参数说明

### vasp/ELF/setup_elf_workflow.py

```
python setup_elf_workflow.py <QE_DIR> [选项]

  qe_dir               QE 计算根目录
  --elf-root           输出根目录（默认: ./vasp/ELF）
  --pattern            子目录匹配（默认: *GPa*）
  --with-poscar        同步生成 POSCAR 到 opt_ELF
  --dry-run            只打印计划，不创建文件
```

### vasp/ELF/make_poscar.py

```
python make_poscar.py <QE体系目录> [--elf-root ./vasp/ELF]

  --scan QE_DIR        批量扫描 QE 目录
  --relax-in PATH      显式指定 relax.in（配合 --base-dir）
  --base-dir PATH      基目录，如 vasp/ELF/Ag/50
  --elf-root           批量/单体系输出根目录（默认: ./vasp/ELF）
  --pattern            子目录匹配（默认: *GPa*）
  --write-pbs          同时写入 ELF.pbs（默认只写 POSCAR）
```

### vasp/ELF/make_potcar.py

```
python make_potcar.py [元素列表] [选项]

  --poscar POSCAR      从 POSCAR 读取元素顺序
  -o, --output         输出路径（默认: POTCAR）
  --pbe-lib            赝势库根目录
  --keep-single        保留每个元素的单独 .POTCAR
  --scan PATH          批量处理根目录下所有 POSCAR
```

### vasp/ELF/submit_opt_elf.py

```
python submit_opt_elf.py [ROOT] [选项]

  root                 根目录（默认: ./vasp/ELF）
  --max-jobs           用户任务数上限（默认: 8）
  --resubmit           清除 .pbs_submitted 标记后重新提交
  --clear-markers      仅删除标记文件，不提交
  --dry-run            只打印计划
```

### vasp/ELF/run_elf_batch.py

```
python run_elf_batch.py <QE_DIR> [选项]

  --elf-root           输出根目录（默认: ./vasp/ELF）
  --pbe-lib            赝势库路径
  --pattern            子目录匹配（默认: *GPa*）
  --skip-existing      POSCAR 和 POTCAR 已存在时跳过
  --dry-run            只打印计划
```

### ELF/run_scf_batch.py

```
python run_scf_batch.py <QE_DIR> [选项]

  --elf-root           输出根目录（默认: ./ELF）
  --pbe-lib            赝势库路径
  --pattern            子目录匹配（默认: *GPa*）
  --skip-existing      POSCAR 和 POTCAR 已存在时跳过
  --dry-run            只打印计划
```

---

## 赝势库路径

默认已配置为：

```
/home/test1/hhy/basic/psudopotential/PAW-GGA-PBE
```

定义位置：`vasp/ELF/vasp_common.py` 中 `DEFAULT_PBE_LIB`。

如需临时更换，可用环境变量或命令行参数：

```bash
export PBE_LIB=/home/test1/hhy/basic/psudopotential/PAW-GGA-PBE
python make_potcar.py --scan ./vasp/ELF --pbe-lib /path/to/PAW-GGA-PBE
```

---

## 输出目录示例

```
vasp/ELF/
└── Ag/
    └── 50/
        └── opt_ELF/
            ├── ELF.pbs      # 结构优化 PBS（Relaxation INCAR）
            ├── POSCAR
            └── POTCAR

ELF/
└── Ag/
    └── 50/
        └── scf_ELF/
            ├── ELF.pbs      # ELF 计算 PBS（LELF=TRUE）
            ├── POSCAR
            └── POTCAR
```

---

## INCAR 设置

**opt_ELF**（结构优化，vasp/ELF 管理）：

| 参数 | 值 | 说明 |
|------|-----|------|
| `SYSTEM` | `Relaxation` | 结构弛豫 |
| `ISIF` | `3` | 优化离子+晶胞 |
| `IBRION` | `2` | 共轭梯度 |
| `NSW` | `200` | 最大离子步 |
| `EDIFFG` | `-0.01` | 力收敛 (eV/Å) |

**scf_ELF**（ELF 计算，ELF/ 管理）：

| 参数 | 值 | 说明 |
|------|-----|------|
| `LELF` | `TRUE` | 输出电子局域函数 |
| `LCHARG` | `TRUE` | 输出电荷密度 |
| `ENCUT` | `800` | 截断能 (eV) |
| `KSPACING` | `0.03` | K 点间距 |

---

## POTCAR 选择规则

对每个元素，在赝势库中搜索以下目录（**源文件始终叫 `POTCAR`，不改动**）：

- `<pbe-lib>/<Element>/POTCAR` — 精确匹配，如 `Ag/POTCAR`
- `<pbe-lib>/<Element>.*/POTCAR` — 数字后缀，如 `H.25/POTCAR`、`H.5/POTCAR`
- `<pbe-lib>/<Element>_*/POTCAR` — 软/硬赝势标识，如 `Ba_sv/POTCAR`、`Li_pv/POTCAR`

### 择优标准（按优先级）

| 优先级 | 标准 | 说明 |
|--------|------|------|
| 1 | **ZVAL 最大** | 价电子数最多者优先（通常 `_sv` > 普通 > `_pv`） |
| 2 | **日期最新** | ZVAL 相同时，取 POTCAR 第一行末尾日期较新者 |

日期格式示例：`PAW_PBE H1.25 07Sep2000` → 取 `07Sep2000`

### 拼接流程

```
赝势库/H.5/POTCAR  ──cp──>  vasp/ELF/Ag/50/opt_ELF/H.POTCAR
                              │
                    cat H.POTCAR Ag.POTCAR
                              v
                  vasp/ELF/Ag/50/opt_ELF/POTCAR
                  ELF/Ag/50/scf_ELF/POTCAR       (独立生成)
```

工作目录中用 `<元素>.POTCAR` 区分各单元素副本，拼接完成后默认删除中间文件。

---

## 依赖与环境

- **Python**：3.8+，仅标准库，无第三方依赖
- **运行环境**：Linux HPC（PBS 作业调度、`module load vasp`）
- **赝势库**：需能访问 PAW-GGA-PBE 目录（默认路径见 `vasp/ELF/vasp_common.py` 中 `DEFAULT_PBE_LIB`）
- **QE 输入**：各体系目录下需存在 `relax.in`（可在子目录中，搜索深度 ≤ 3）
- **模块导入**：
  - `vasp/ELF/` 脚本导入同目录 `vasp_common`
  - `ELF/` 脚本导入同目录 `scf_common`，后者通过 `sys.path` 引用 `vasp/ELF/vasp_common`

---

## 常见问题

**Q: 找不到 relax.in？**  
确认 QE 体系目录下存在 `relax.in`，且路径深度不超过 3 层。

**Q: POTCAR 失败后 POSCAR 还在吗？**  
在。往期 bug（POTCAR 失败时 `rm -rf` 整个目录）已修复：**POTCAR 失败时保留 POSCAR**。

**Q: 报错 `ERROR: no POTCAR for H`？**  
H 的赝势目录通常为 `H.25`、`H.5` 等点号命名。新版脚本已支持 `H.*` 搜索。

**Q: 文件夹名解析失败？**  
确认命名符合 `<材料>-...-<压强信息>-<温度>K` 格式，且子目录名包含 `GPa`。

**Q: 只想重建 POTCAR？**  
```bash
python vasp/ELF/make_potcar.py --scan ./vasp/ELF
```
