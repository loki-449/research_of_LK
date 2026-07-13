# VASP 计算模块

从 QE 前处理到 VASP 结构优化（opt）→ SCF + ELF 计算的全流程部署工具。

## 先读这个

**[`../VASP_QUICKSTART.md`](../VASP_QUICKSTART.md)**：MVP → 高通量 → 分脚本（与 AIMD 上手文档同构）。

## 目录说明

| 路径 | 类型 | 说明 |
|------|------|------|
| `scripts/` | **脚本包** | 可安装到任意位置，不含计算数据 |
| `deploy.env.example` | **部署配置模板** | 复制为 `deploy.env` 后按本机修改 |
| `CLAUDE.md` | Agent 指令 | Cursor / Claude 对话路由用 |

计算数据**不**放在本目录，而在独立的工作根目录 `<work_root>/` 下。

## 快速部署（集群）

```bash
# 1. 安装脚本包
mkdir -p /home/test1/hhy/tools/vasp
cp -r scripts/ /home/test1/hhy/tools/vasp/scripts/

# 2. 配置环境
cd /home/test1/hhy/calculation/vasp
cp deploy.env.example deploy.env
vim deploy.env

# 3. 加载配置（写入 ~/.bashrc 可永久生效）
source deploy.env
export VASP_DEPLOY_ENV=/home/test1/hhy/calculation/vasp/deploy.env

# 4. 运行（示例）
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/setup_opt_workflow.py $QE_ROOT
```

## 部署配置一览

| 变量 | 默认值（example） | 含义 |
|------|-------------------|------|
| `VASP_SCRIPTS_ROOT` | `/home/test1/hhy/tools/vasp/scripts` | 脚本安装根 |
| `VASP_WORK_ROOT` | `/home/test1/hhy/calculation/vasp_work` | 计算数据根 |
| `QE_ROOT` | `/home/test1/hhy/calculation/QE` | QE 输入目录 |
| `PBE_LIB` | `/home/test1/hhy/basic/psudopotential/PAW-GGA-PBE` | 赝势库 |
| `VASP_PYTHON` | `python3` | Python 解释器 |
| `VASP_DEPLOY_ENV` | — | 指向 deploy.env，脚本启动时自动加载 |
| `VASP_SUBMIT_MAX_JOBS` | `8` | PBS 并发上限 |
| `VASP_SUBMIT_WAIT_INTERVAL` | `60` | 队列满时重试间隔（秒） |

完整说明见 [deploy.env.example](deploy.env.example)。

## 计算数据目录结构

```
/home/test1/hhy/calculation/vasp_work/     ← VASP_WORK_ROOT
├── Ag/
│   └── 50/
│       ├── opt/          ← 结构优化（POSCAR, POTCAR, opt.pbs, CONTCAR）
│       └── scf_ELF/      ← ELF 计算（POSCAR, POTCAR, ELF.pbs）
└── Ag-H/
    └── 80/
        ├── opt/
        └── scf_ELF/
```

## 工作流

```
QE relax.in  ──→  opt 结构优化  ──→  scf_ELF (LELF=TRUE)
   (QE_ROOT)      (WORK_ROOT)         (WORK_ROOT)
```

### 分步执行

```bash
source deploy.env

# opt
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/setup_opt_workflow.py $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_poscar.py --scan $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_potcar.py --scan $VASP_WORK_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py

# scf_ELF（opt 完成后）
$VASP_PYTHON $VASP_SCRIPTS_ROOT/scf_ELF/scf_contcar_to_poscar_ELF.py --scan --write-pbs
```

## 子模块文档

| 层级 | README |
|------|--------|
| 脚本包 | [scripts/README.md](scripts/README.md) |
| 公共库 | [scripts/lib/README.md](scripts/lib/README.md) |
| 结构优化 | [scripts/opt/README.md](scripts/opt/README.md) |
| ELF 计算 | [scripts/scf_ELF/README.md](scripts/scf_ELF/README.md) |

## 运行环境

- Linux HPC，PBS 作业调度
- Python 3.8+，仅标准库
- VASP（Intel oneAPI 编译版）
- 模块：`gcc/9.1.0`, `intel/intel2018`, `oneapi/*`, `vasp`
