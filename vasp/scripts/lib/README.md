# lib — 公共库

VASP 工作流共享 Python 模块，被 `opt/` 与 `scf_ELF/` 入口脚本引用。

## 模块清单

| 文件 | 职责 |
|------|------|
| `bootstrap.py` | 初始化 import 路径，可选加载 deploy.env |
| `path_config.py` | 工作根 / 脚本根路径解析，环境变量常量 |
| `vasp_common.py` | QE 解析、POSCAR/POTCAR、PBS 模板、opt 目录管理 |
| `scf_common.py` | SCF + ELF INCAR、scf_ELF 目录管理 |

## 配置

见 [config.env.example](config.env.example)。主要环境变量：

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `PBE_LIB` | 赝势库路径 | `/home/test1/hhy/basic/psudopotential/PAW-GGA-PBE` |
| `VASP_WORK_ROOT` | 计算数据根 | 见 deploy.env |
| `VASP_SCRIPTS_ROOT` | 脚本安装根 | 自动检测或 env 指定 |
| `VASP_DEPLOY_ENV` | deploy.env 路径 | 未设置则不自动加载 |

### 路径解析优先级（work root）

```
--work-root  >  VASP_WORK_ROOT  >  当前工作目录
```

## 物理默认值

### opt（vasp_common.OPT_INCAR）

| 参数 | 值 |
|------|-----|
| ENCUT | 800 eV |
| ISIF | 3 |
| IBRION | 2 |
| NSW | 200 |
| EDIFFG | -0.01 |
| KSPACING | 0.03 |

### scf_ELF（scf_common.SCF_INCAR）

| 参数 | 值 |
|------|-----|
| ENCUT | 800 eV |
| LELF | TRUE |
| LCHARG | TRUE |
| KSPACING | 0.02 |

### POTCAR 择优

1. ZVAL（价电子数）最大者优先
2. ZVAL 相同时，POTCAR 第一行日期最新者

## 核心 API

### path_config

```python
from path_config import resolve_work_root, scripts_root, load_deploy_env, script_path

work = resolve_work_root()                    # 当前工作根
scripts = scripts_root()                      # 脚本安装根
load_deploy_env("/path/to/deploy.env")        # 加载配置
script_path("opt", "submit_opt.py")           # 拼接脚本路径
```

### vasp_common

```python
from vasp_common import (
    parse_qe_system,          # 解析 Ag-H-50GPa-300K 命名
    deploy_opt_system,        # opt 一键部署
    iter_opt_work_dirs,       # 扫描 <work_root>/*/opt/
    system_base_dir,          # work_root/Ag/50
)
```

### scf_common

```python
from scf_common import deploy_scf_system, setup_scf_scripts
```

## QE 体系命名规则

文件夹名格式：`<材料>-<压强信息>-<温度>K`

示例：`Ag-H-50GPa-300K` → 材料=`Ag`，压强=`50`，温度=`300`

## 扩展说明

- 新增公共功能应写入 `vasp_common.py` 或 `scf_common.py`
- 不要在 lib 中硬编码计算数据路径
- 入口脚本通过 `bootstrap.init_imports()` 导入本目录，无需 pip install
