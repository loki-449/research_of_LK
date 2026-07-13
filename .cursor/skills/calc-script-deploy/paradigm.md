# 脚本部署内容范式（技能详表）

Agent 在 Step 3 填写下表后再写代码。仓库级完整版见 `SCRIPT_DEPLOY_PARADIGM.md`。

---

## A. 规格总表（每个新脚本包必填）

### A1. 元信息

| 项 | 填写 |
|----|------|
| 模块名 | 如 vasp / AIMD / 新模块 |
| 子阶段 | 如 opt / scf_ELF |
| 脚本安装根变量 | 如 `VASP_SCRIPTS_ROOT` |
| 计算工作根变量 | 如 `VASP_WORK_ROOT` |
| 输入根变量 | 如 `QE_ROOT` |
| deploy 配置文件 | `deploy.env` / `*.env.example` |

### A2. 路径三类（防混淆）

| 类型 | 典型路径 | 可否删除 |
|------|----------|----------|
| 脚本包目录 | `$SCRIPTS_ROOT/<stage>/` | ❌ |
| 计算数据目录 | `$WORK_ROOT/<体系>/<stage>/` | 慎删（有数据时） |
| 遗留/空目录 | 重构前旧路径 | ✅ 若逻辑不用 |

### A3. 逻辑链条

```
模板输入 ──→ [脚本A] ──→ 生成物1 @ 路径1
                │
                ▼
             [脚本B] ──→ 生成物2 @ 路径2
                │
                ▼
            (外部引擎) ──→ 运行产物 @ 路径3
```

### A4. 单脚本规格卡

每个入口脚本一张：

| 项 | 内容 |
|----|------|
| 文件 | `scripts/<stage>/<name>.py` |
| 用途 | 一句话 |
| 命令 | `$PY $SCR/...` 完整示例 |
| 输入 | 文件/目录 + 必须存在的前置条件 |
| CLI 参数 | 与 `--help` 一致；写出默认值 |
| 环境变量 | 读写哪些；是否依赖 `source deploy.env` |
| 依赖库 | `import` 的 common 函数（**参数名必须与函数签名一致**） |
| 生成物 | 文件名 → 绝对路径模式 |
| 不生成 | 明确列出，避免用户误以为脚本会产出 |
| dry-run | 是否支持 |

### A5. 案例模板数据（MVP）

| 项 | 示例（VASP opt） |
|----|------------------|
| 最小输入 | 1 个 QE 目录：`Ba3AgH7-H-10GPa-300K/relax.in` |
| 命名规则 | `材料-…-压强GPa-温度K` |
| 工作根 | `$WORK_ROOT/Ba3AgH7/10/opt/` |
| 期望产物 | `opt.pbs`, `POSCAR`, `POTCAR` |
| 赝势/依赖 | `$PBE_LIB` 含 Ba/Ag/H |
| 成功判据 | 三文件存在且非空；`--dry-run` 无异常 |

### A6. 批判清单（写代码前勾选）

- [ ] shell `$VAR/path` 在 VAR 为空时会变成绝对路径 `/path` 吗？
- [ ] common 函数关键字参数名与调用处一致吗？
- [ ] 批量循环里异常会被静默吞掉还是崩掉？应捕获并继续吗？
- [ ] 一键脚本与分步脚本生成物是否等价？
- [ ] README / WORKFLOW / `--help` 是否同步？
- [ ] 下游是否假定上游产物已存在并写清前置条件？

---

## B. README 撰写范式

对齐现有 `vasp/scripts/opt/README.md`：

```markdown
# <stage> — <一句话>

## 配置
| 变量 | 默认 | 说明 |

## 输出目录
（树状列出生成物，标注谁生成 / VASP 生成）

## 脚本清单
| 脚本 | 用途 |

## 推荐工作流（分步）
（可复制 bash，含 source deploy.env）

## 一键（可选）

## 常用参数
（与 argparse / --help 一致）

## 故障排查
| 现象 | 处理 |

## 上游 / 下游
```

---

## C. WORKFLOW 文档范式

对齐 `VASP_WORKFLOW.md`：

1. 路径三类辨析  
2. 环境变量表  
3. **全部脚本**：用法 · 生成物 · 路径 · 依赖 · 不生成  
4. 关联图 + 调用关系表 + 数据依赖链  
5. 标准流程命令  
6. 目录产物对照表  
7. **回答范式模板**（Agent 复用）

---

## D. 手册范式（Step 4）

### D0. 上手三层（主目录 / 模块入口必有）

顺序固定，见仓库根 `SCRIPT_DEPLOY_PARADIGM.md` §5.5；样例：`VASP_QUICKSTART.md`、`AIMD_QUICKSTART.md`。

1. MVP 计算流程  
2. 高通量计算流程  
3. 分脚本单独运行流程  

### D1. 简易使用卡（给集群即时查阅）

```markdown
# <模块> 一页卡
1. source <deploy.env>
2. echo SCR=[$SCRIPTS_ROOT]   # 非空
3. <3–5 条核心命令>
4. 成功标志：<ls 期望文件>
5. 常见失败：VAR 空 → /opt/xxx.py；缺 PBE_LIB；无 CONTCAR
```

### D2. 详细手册

含：路径说明、分步/一键、参数表、产物表、故障排查、与 WORKFLOW 交叉引用。

---

## E. argparse / 环境变量约定

| 约定 | 规则 |
|------|------|
| 工作根 | 统一 `--work-root`；废弃别名可 `SUPPRESS` |
| 扫描 | `--scan` 批量；位置参数单体系 |
| 幂等 | `--skip-existing` / 提交标记文件 |
| 安全 | `--dry-run` 优先提供 |
| env | `export NAME=value`；Python `load_deploy_env` 不覆盖已有变量 |
| 帮助 | docstring「基本用法」与 README 命令块同源 |

---

## F. VASP 对照锚点（实现时参考）

| 阶段 | 入口 | 数据路径 |
|------|------|----------|
| 环境 | `deploy.env` + `install.sh` | — |
| opt | `scripts/opt/*` | `$WR/<A>/<B>/opt/` |
| scf_ELF | `scripts/scf_ELF/*` | `$WR/<A>/<B>/scf_ELF/` |
| 公共 | `scripts/lib/*` | 不写计算数据 |
