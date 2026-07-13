# opt — 结构优化部署

从 QE `relax.in` 生成 VASP 结构优化输入，提交 PBS 任务。

## 配置

见 [config.env.example](config.env.example)：

| 变量 | 默认 | 说明 |
|------|------|------|
| `VASP_SUBMIT_MAX_JOBS` | 8 | 同时运行的 PBS 任务上限 |
| `VASP_SUBMIT_WAIT_INTERVAL` | 60 | 队列满时等待秒数 |
| `VASP_QE_PATTERN` | `*GPa*` | QE 子目录匹配模式 |

## 输出目录

```
$VASP_WORK_ROOT/<材料>/<压强>/opt/
├── opt.pbs       ← PBS 提交脚本（Relaxation INCAR）
├── POSCAR
├── POTCAR
├── CONTCAR       ← VASP 运行后生成
└── .pbs_submitted ← 提交标记（防重复 qsub）
```

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `setup_opt_workflow.py` | 建立目录 + 写 opt.pbs |
| `make_poscar.py` | 从 relax.in 生成 POSCAR |
| `make_potcar.py` | 拼接 POTCAR |
| `run_opt_batch.py` | 一键：目录 + PBS + POSCAR + POTCAR |
| `submit_opt.py` | 批量 qsub |

## 推荐工作流（分步）

```bash
source deploy.env

# ① 建目录 + PBS
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/setup_opt_workflow.py $QE_ROOT

# ② 生成 POSCAR
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_poscar.py --scan $QE_ROOT

# ③ 拼接 POTCAR
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/make_potcar.py --scan $VASP_WORK_ROOT

# ④ 提交 PBS
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py
```

## 一键批量

```bash
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/run_opt_batch.py $QE_ROOT
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py
```

## 常用参数

### setup_opt_workflow.py

```bash
python setup_opt_workflow.py $QE_ROOT \
    --work-root $VASP_WORK_ROOT \
    --pattern '*GPa*' \
    --with-poscar        # 同时写 POSCAR
```

### make_poscar.py

```bash
# 批量
python make_poscar.py --scan $QE_ROOT --work-root $VASP_WORK_ROOT

# 单个 QE 目录
python make_poscar.py /path/to/Ag-H-50GPa-300K

# 指定 relax.in + 目标体系
python make_poscar.py \
    --relax-in /path/to/relax.in \
    --base-dir $VASP_WORK_ROOT/Ag/50
```

### make_potcar.py

```bash
python make_potcar.py --scan $VASP_WORK_ROOT
python make_potcar.py --poscar $VASP_WORK_ROOT/Ag/50/opt/POSCAR \
    -o $VASP_WORK_ROOT/Ag/50/opt/POTCAR
```

### submit_opt.py

```bash
python submit_opt.py                          # 使用 VASP_WORK_ROOT
python submit_opt.py $VASP_WORK_ROOT
python submit_opt.py --max-jobs 4 --resubmit  # 清除标记重新提交
python submit_opt.py --dry-run                # 只打印计划
```

## PBS 脚本说明

`opt.pbs` 内嵌 INCAR（ISIF=3 全弛豫），加载模块：

```
gcc/9.1.0, intel/intel2018, oneapi/compiler, oneapi/mpi, oneapi/mkl, vasp
mpirun -np 64 vasp_std
```

## 故障排查

| 现象 | 处理 |
|------|------|
| POTCAR 失败 | POSCAR 和 opt.pbs 保留，检查 `PBE_LIB` 路径 |
| qsub 失败 | 确认在 PBS 登录节点运行，`qstat` 可用 |
| 重复提交被跳过 | 删除 `opt/.pbs_submitted` 或使用 `--resubmit` |
| 目录未创建 | 先运行 `setup_opt_workflow.py`，检查 QE 文件夹命名 |

## 下一步

opt 完成后 CONTCAR 就绪，进入 [scf_ELF 工作流](../scf_ELF/README.md)。
