# VASP 计算模块（总入口）

## 模块定位
本目录负责所有 VASP 计算相关的脚本部署，涵盖从 QE 前处理结果到 VASP 输入文件生成、PBS 提交、轨迹后处理的全流程。

## 开发/部署前（强制）
新增阶段或改脚本前：根目录 `README.md` 四步 + `SCRIPT_DEPLOY_PARADIGM.md` 规格表。  
**日常上手优先**：根目录 [`VASP_QUICKSTART.md`](../VASP_QUICKSTART.md)。  
完整用法查询：[`VASP_WORKFLOW.md`](../VASP_WORKFLOW.md)。  
Agent 技能：`.cursor/skills/calc-script-deploy/`。

## 两类路径（必须分开）

| 类型 | 说明 | 示例 |
|------|------|------|
| **脚本安装路径** | 可整体拷贝/deploy 的 Python 工具，与计算数据无关 | `/opt/vasp-tools/scripts/` |
| **计算工作路径** | 实际存放输入/输出数据的根目录 | `/home/user/project/calc/` |

脚本路径由安装位置决定；工作路径通过 **`--work-root`** 或环境变量 **`VASP_WORK_ROOT`** 指定（未指定时使用当前工作目录）。

**部署文档**: 见 [README.md](README.md) 与 [deploy.env.example](deploy.env.example)。

## 目录架构

**脚本包**（`vasp/scripts/`，可安装到任意位置）:
```
vasp/scripts/
├── lib/                          ← 公共库（vasp_common / scf_common / path_config）
├── opt/                          ← 结构优化入口脚本
│   ├── setup_opt_workflow.py
│   ├── make_poscar.py
│   ├── make_potcar.py
│   ├── run_opt_batch.py
│   └── submit_opt.py
└── scf_ELF/                      ← SCF + ELF 入口脚本
    ├── scf_contcar_to_poscar_ELF.py
    └── run_scf_batch.py
```

**计算数据**（位于工作根目录 `<work_root>/`，与脚本路径无关）:
```
<work_root>/
├── Ag/
│   └── 50/
│       ├── opt/                  ← 结构优化
│       └── scf_ELF/              ← ELF 计算
└── ...
```

## 部署到其他机器

```bash
# 1. 拷贝脚本包
scp -r vasp/scripts/ user@cluster:/opt/vasp-tools/scripts/

# 2. 在集群上设置工作目录（可写入 ~/.bashrc）
export VASP_WORK_ROOT=/home/user/my_calc
export PBE_LIB=/path/to/PAW-GGA-PBE

# 3. 从任意目录调用（脚本路径与工作路径无关）
python /opt/vasp-tools/scripts/opt/setup_opt_workflow.py /path/to/QE_folder
python /opt/vasp-tools/scripts/opt/submit_opt.py
```

## 推荐工作流

### 结构优化（opt）
```bash
export VASP_WORK_ROOT=/home/user/my_calc   # 或每次加 --work-root

python /opt/vasp-tools/scripts/opt/setup_opt_workflow.py /path/to/QE_folder
python /opt/vasp-tools/scripts/opt/make_poscar.py --scan /path/to/QE_folder
python /opt/vasp-tools/scripts/opt/make_potcar.py --scan $VASP_WORK_ROOT
python /opt/vasp-tools/scripts/opt/submit_opt.py
```

### SCF + ELF
```bash
python /opt/vasp-tools/scripts/scf_ELF/scf_contcar_to_poscar_ELF.py --scan --write-pbs
```

## 跨子模块约定
- 公共库位于 `scripts/lib/`，入口脚本通过 `bootstrap.py` 自动配置 import 路径
- 工作根下按 `<材料>/<压强>/` 组织，每个体系下 `opt/` 与 `scf_ELF/` 并列
- 赝势库：`PBE_LIB` 环境变量或 `--pbe-lib`
- 工作流顺序：**opt → scf_ELF → (未来) scf_bader**

## 注意事项
- 不要在脚本安装目录下存放计算数据
- 优先使用分步脚本，便于定位问题
- `submit_opt.py` 通过 `.pbs_submitted` 标记防重复提交
