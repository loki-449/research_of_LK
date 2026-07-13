# scf_ELF — SCF + ELF 计算部署

从 opt 优化后的 CONTCAR 部署 ELF 计算（LELF=TRUE）。

## 配置

见 [config.env.example](config.env.example)：

| 变量 | 默认 | 说明 |
|------|------|------|
| `VASP_SCF_WRITE_PBS` | 1 | 批量转换 CONTCAR 时是否写 ELF.pbs |

## 输入 / 输出

```
输入:  $VASP_WORK_ROOT/<材料>/<压强>/opt/CONTCAR
输出:  $VASP_WORK_ROOT/<材料>/<压强>/scf_ELF/
         ├── POSCAR    ← 由 CONTCAR 复制
         ├── ELF.pbs   ← LELF=TRUE INCAR
         ├── POTCAR    ← run_scf_batch 生成
         └── ELFCAR    ← VASP 运行后生成
```

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `scf_contcar_to_poscar_ELF.py` | CONTCAR → scf_ELF/POSCAR（主流程） |
| `run_scf_batch.py` | 从 QE relax.in 一键部署 scf_ELF |
| `elf_common.py` | 向后兼容 import 包装 |
| `remove_xcursor.py` | 清理 ELFCAR 目录中的 xcursor.png |

## 推荐工作流

opt 计算完成、CONTCAR 存在后：

```bash
source deploy.env

# ① CONTCAR → scf_ELF/POSCAR，并写 ELF.pbs
$VASP_PYTHON $VASP_SCRIPTS_ROOT/scf_ELF/scf_contcar_to_poscar_ELF.py \
    --scan --write-pbs

# ② 手动进入 scf_ELF 目录提交（或自行写批量提交脚本）
cd $VASP_WORK_ROOT/Ag/50/scf_ELF
qsub ELF.pbs
```

## 常用命令

### 批量扫描

```bash
python scf_contcar_to_poscar_ELF.py --scan --write-pbs
python scf_contcar_to_poscar_ELF.py --scan --work-root /path/to/calc
```

### 单个体系

```bash
python scf_contcar_to_poscar_ELF.py \
    --system-dir $VASP_WORK_ROOT/Ag/50 \
    --write-pbs
```

### 指定文件

```bash
python scf_contcar_to_poscar_ELF.py \
    --contcar $VASP_WORK_ROOT/Ag/50/opt/CONTCAR \
    --output $VASP_WORK_ROOT/Ag/50/scf_ELF/POSCAR \
    --write-pbs
```

### 从 QE 直接部署 scf（不依赖 CONTCAR）

适用于跳过 opt、直接用 QE 结构做 ELF 的场景：

```bash
python run_scf_batch.py $QE_ROOT --work-root $VASP_WORK_ROOT
```

## INCAR 要点（ELF.pbs）

| 参数 | 值 |
|------|-----|
| LELF | TRUE |
| LCHARG | TRUE |
| ENCUT | 800 eV |
| KSPACING | 0.02 |
| ISMEAR | 1, SIGMA=0.02 |

## 故障排查

| 现象 | 处理 |
|------|------|
| CONTCAR 未找到 | 确认 opt 已收敛完成 |
| scf_ELF 目录不存在 | 加 `--write-pbs` 会自动创建 |
| POSCAR 元素顺序 | 直接复制 CONTCAR，与 opt 一致 |

## 上游 / 下游

- 上游：[opt 结构优化](../opt/README.md)
- 下游：Bader 电荷分析（`opt_scf_bader/`，待部署）
