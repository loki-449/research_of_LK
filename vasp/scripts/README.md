# VASP 脚本包（scripts/）

可整体拷贝到集群的 Python 工具包。**本目录只放脚本，不放计算数据。**

## 安装

```bash
# 目标路径（与 deploy.env 中 VASP_SCRIPTS_ROOT 一致）
INSTALL=/home/test1/hhy/tools/vasp/scripts

mkdir -p $(dirname $INSTALL)
cp -r scripts/ $INSTALL/

# 验证
$VASP_PYTHON $INSTALL/opt/setup_opt_workflow.py --help
```

## 目录结构

```
scripts/
├── README.md           ← 本文件
├── lib/                ← 公共库（vasp_common, scf_common, path_config）
├── opt/                ← 结构优化入口脚本
└── scf_ELF/            ← SCF + ELF 入口脚本
```

## 路径机制

| 概念 | 配置方式 | 示例 |
|------|----------|------|
| 脚本在哪 | 安装位置 / `VASP_SCRIPTS_ROOT` | `/home/test1/hhy/tools/vasp/scripts` |
| 数据在哪 | `VASP_WORK_ROOT` / `--work-root` | `/home/test1/hhy/calculation/vasp_work` |

脚本启动时 `bootstrap.py` 会：

1. 若设置了 `VASP_DEPLOY_ENV`，自动加载 deploy.env
2. 将 `lib/`、`opt/`、`scf_ELF/` 加入 Python 路径

## 部署配置层级

```
vasp/deploy.env.example          ← 主配置（路径 + 全局变量）
scripts/lib/config.env.example   ← lib 层默认值说明
scripts/opt/config.env.example   ← opt 层（PBS 并发等）
scripts/scf_ELF/config.env.example ← scf 层
```

推荐做法：只维护一份 `deploy.env`，按需追加 `source` 子模块配置：

```bash
# deploy.env 末尾
source /home/test1/hhy/tools/vasp/scripts/opt/config.env
```

## 调用方式

**方式 A：环境变量（推荐）**

```bash
source /path/to/deploy.env
$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/submit_opt.py
```

**方式 B：绝对路径 + 显式 work-root**

```bash
python3 /opt/vasp/scripts/opt/setup_opt_workflow.py \
    /path/to/QE --work-root /path/to/calc
```

**方式 C：cd 到工作目录**

```bash
cd /home/test1/hhy/calculation/vasp_work
python3 /opt/vasp/scripts/opt/make_potcar.py --scan .
```

## 子目录文档

- [lib/README.md](lib/README.md) — 公共库 API 与物理默认值
- [opt/README.md](opt/README.md) — 结构优化分步工作流
- [scf_ELF/README.md](scf_ELF/README.md) — ELF 计算工作流

## 注意事项

- 不要在 `scripts/` 下创建 `Ag/`、`50/` 等计算目录
- 升级脚本：覆盖 `scripts/` 目录即可，不影响 `VASP_WORK_ROOT` 中的数据
- 所有脚本依赖 `lib/bootstrap.py` 引导 import，不要单独移动某个 `.py` 文件
