# VASP 计算模块（总入口）

## 模块定位
本目录负责所有 VASP 计算相关的脚本部署，涵盖从 QE 前处理结果到 VASP 输入文件生成、PBS 提交、轨迹后处理的全流程。

## 子模块架构

```
vasp/
├── CLAUDE.md                     ← 本文件（VASP 总入口）
├── opt/                          ← ① 结构优化（opt_ELF）
│   ├── vasp_common.py            ← 共享核心库（QE 解析 / POSCAR / POTCAR / PBS）
│   ├── setup_elf_workflow.py
│   ├── make_poscar.py
│   ├── make_potcar.py
│   ├── run_elf_batch.py
│   └── submit_opt_elf.py
├── scf_ELF/                      ← ② SCF + ELF 计算
│   ├── scf_common.py             ← 导入 vasp_common
│   ├── scf_contcar_to_poscar_ELF.py
│   └── run_scf_batch.py
└── opt_scf_bader/                ← ③ 未来扩展：Bader 电荷分析
    └── (待部署)
```

## 子模块功能

### ① vasp/opt/ — 结构优化
从 QE relax.in 批量生成 VASP 输入文件，部署 opt_ELF 计算。

**输入**: QE 体系文件夹（`<材料>-<压强>-<温度>K`，内含 `relax.in`）
**输出**: `vasp/opt/<材料>/<压强>/opt_ELF/{ELF.pbs, POSCAR, POTCAR}`

**触发词**: "部署 opt"、"结构优化"、"run elf batch"、"submit opt"、"生成 POSCAR"、"拼接 POTCAR"

**推荐工作流**:
```bash
cd vasp/opt
python setup_elf_workflow.py /path/to/QE_folder           # ① 建立目录 + PBS
python make_poscar.py --scan /path/to/QE_folder            # ② 生成 POSCAR
python make_potcar.py --scan ./vasp/opt                     # ③ 拼接 POTCAR
python submit_opt_elf.py ./vasp/opt                         # ④ 提交任务
# 或一键: python run_elf_batch.py /path/to/QE_folder
```

**INCAR**: ISIF=3, IBRION=2, NSW=200, EDIFFG=-0.01, ENCUT=800, KSPACING=0.02

### ② vasp/scf_ELF/ — SCF + ELF 计算
从 opt_ELF 优化后的 CONTCAR 部署 ELF 计算。

**输入**: `vasp/opt/<材料>/<压强>/opt_ELF/CONTCAR`
**输出**: `vasp/scf_ELF/<材料>/<压强>/scf_ELF/{ELF.pbs, POSCAR, POTCAR}`

**触发词**: "CONTCAR 转 POSCAR"、"部署 scf"、"ELF 计算"、"contcar to poscar"

**推荐工作流**:
```bash
cd vasp/scf_ELF
python scf_contcar_to_poscar_ELF.py --scan --write-pbs      # ① CONTCAR → POSCAR
#  或一键: python run_scf_batch.py /path/to/QE_folder --elf-root ./vasp/scf_ELF
```

**INCAR**: LELF=TRUE, LCHARG=TRUE, ENCUT=800, KSPACING=0.02

### ③ vasp/opt_scf_bader/ — Bader 电荷分析（待部署）
从 scf 计算结果做 Bader 电荷布居分析，输出 ACF 数据与汇总。

## 跨子模块约定
- 所有子模块共享 `vasp/opt/vasp_common.py` 中的核心工具（QE 解析、赝势库、PBS 模板）
- 体系命名统一：`<材料>/<压强>/`（如 `Ag/50/`）
- 赝势库默认路径：`/home/test1/hhy/basic/psudopotential/PAW-GGA-PBE`
- POTCAR 择优规则：ZVAL 最大优先，日期最新次之
- 工作流顺序：**opt → scf_ELF → (未来) scf_bader**，后一步依赖前一步的输出

## 注意事项
- 目录建立先于文件部署，部分失败不删已有文件
- 优先使用分步脚本，便于定位问题
- POTCAR 生成失败时保留已有 POSCAR 和 PBS
- `submit_opt_elf.py` 通过 `.pbs_submitted` 标记防重复提交
