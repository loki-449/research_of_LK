# 脚本部署内容范式（仓库级完整版）

> **定位**：所有「新建 / 重构计算部署脚本」任务的统一规格与文档模板。  
> **配套**：根 [`README.md`](README.md) 强制四步流程；Cursor 技能 `.cursor/skills/calc-script-deploy/`；  
> **范例实现**：[`VASP_WORKFLOW.md`](VASP_WORKFLOW.md) + `vasp/scripts/**/README.md`；  
> **上手样例（MVP→高通量→分脚本）**：[`VASP_QUICKSTART.md`](VASP_QUICKSTART.md)、[`AIMD_QUICKSTART.md`](AIMD_QUICKSTART.md)。

---

## 0. 何时使用本范式

| 场景 | 是否套用 |
|------|----------|
| 新阶段脚本（如 scf_bader） | ✅ |
| 重构脚本目录 / 合并公共库 | ✅ |
| 只问现有脚本怎么用 | ❌ → 直接按 WORKFLOW §回答范式 |
| 纯物理讨论、无部署 | ❌ |

**编码禁令**：未完成「询问流程 → 批判修订 → 规格表」三步前，不创建脚本文件。

---

## 1. 强制流程（与根 README 一致）

```
用户问题
  │
  ▼
① 拆解 + 询问大体工作流 ──用户确认──┐
  │                               │
  ▼                               │
② 批判漏洞/遗漏 ──讨论修订──定稿流程 │
  │                               │
  ├─ 非脚本任务 → 按定稿执行 ◄────┘
  │
  ▼
③ 脚本部署：填本范式规格 → 批判逻辑洞 → 再写代码 + README/help/WORKFLOW
  │
  ▼
④ MVP 测试 → 集群系统测 → 简易使用卡 + 详细手册
```

---

## 2. 从现有脚本抽象出的「规范化对象」

对齐 `vasp/scripts` 已验证结构。

### 2.1 目录骨架

```
<module>/
├── deploy.env.example          # 环境变量模板（export NAME=value）
├── CLAUDE.md                   # 模块路由
├── README.md                   # 模块总览 + 快速部署
└── scripts/
    ├── install.sh              # 可选：拷贝到 $SCRIPTS_ROOT
    ├── README.md
    ├── lib/                    # 公共库（不直接跑）
    │   ├── bootstrap.py
    │   ├── path_config.py
    │   ├── *_common.py
    │   ├── config.env.example
    │   └── README.md
    └── <stage>/                # 入口脚本
        ├── *.py
        ├── config.env.example
        └── README.md
```

### 2.2 环境变量层

| 层级 | 文件 | 作用 |
|------|------|------|
| 主配置 | `deploy.env`（由 example 复制） | `SCRIPTS_ROOT` / `WORK_ROOT` / 输入根 / 解释器 |
| 自动加载 | `*_DEPLOY_ENV` 指向 deploy.env | `bootstrap` → `load_deploy_env`（**不覆盖已有**） |
| 子模块 | `scripts/<stage>/config.env.example` | PBS 并发等可选 |

**关键坑**：终端命令 `$SCRIPTS_ROOT/opt/foo.py` 依赖 **shell `source`**；仅靠 Python 内部 load **不能**展开空变量（会变成 `/opt/foo.py`）。

### 2.3 路径三类（必须写进 WORKFLOW）

| 名称 | 性质 | 删除策略 |
|------|------|----------|
| 脚本包目录 | 仓库/安装态代码 | 不可删 |
| 计算数据目录 | `$WORK_ROOT/...` 运行态 | 有数据则勿删 |
| 遗留空目录 | 重构残留 | 逻辑不用则可删 |

### 2.4 CLI 规范化

| 模式 | 约定 |
|------|------|
| 工作根 | `--work-root`；优先级 CLI > env > cwd |
| 批量 | `--scan` |
| 安全 | `--dry-run`；提交类 `--resubmit` / 标记文件 |
| 帮助 | `argparse` + 文件头 docstring「基本用法」与 README 同源 |
| 库调用 | **关键字参数名 = 函数签名**（反例：`keep_single` ≠ `keep_single_files`） |

### 2.5 README 章节顺序（标准）

1. 一句话定位  
2. 配置（变量表）  
3. 输入/输出目录树（标注生成者）  
4. 脚本清单  
5. 推荐工作流（分步，含 `source deploy.env`）  
6. 一键（可选）  
7. 常用参数（与 `--help` 一致）  
8. 故障排查表  
9. 上游/下游  

参考：`vasp/scripts/opt/README.md`、`vasp/scripts/scf_ELF/README.md`。

### 2.6 WORKFLOW 文档章节顺序（标准）

对齐 `VASP_WORKFLOW.md`：

0. 路径三类  
1. 阶段在总流程中的位置  
2. 环境变量  
3. **全部脚本**：用法 · 生成物 · 路径 · 依赖 · 不生成  
4. 关联图 + 调用表 + 数据依赖链  
5. 标准使用流程  
6. 目录产物对照表  
7. **回答范式**（Agent/人工复用）  
8. 相关文件索引  

---

## 3. Step 3 必填规格表（复制填写）

### 3.1 元信息

```
模块: ________
阶段: ________
SCRIPTS_ROOT 变量: ________
WORK_ROOT 变量: ________
输入根变量: ________
deploy 文件: ________
```

### 3.2 案例模板数据（MVP）

```
体系命名规则: ________
最小输入文件: ________
最小目录树: ________
依赖外部库路径: ________
成功判据: ________
```

### 3.3 逻辑链条

```
<input> --[script_1]--> <artifact_1 @ path_1>
                      --[script_2]--> <artifact_2 @ path_2>
                      --[engine]----> <runtime_out @ path_3>
```

### 3.4 单脚本卡片（每个入口一张）

```
脚本文件:
用途:
命令示例:
输入 / 前置条件:
CLI 参数（名=默认）:
环境变量:
依赖 common 函数（核对签名）:
生成物 → 路径:
明确不生成:
是否 --dry-run:
```

### 3.5 批判清单

- [ ] 空环境变量导致错误绝对路径？  
- [ ] 函数关键字参数名一致？  
- [ ] 批量失败是否应捕获继续？  
- [ ] 分步与一键产物是否等价？  
- [ ] README / WORKFLOW / help 三同步？  
- [ ] 下游前置产物是否写清？  
- [ ] 脚本目录与数据目录是否分离？  

**全部勾选后再写代码。**

---

## 4. 文档输出清单（Step 3 同步交付）

| 产物 | 是否必须 |
|------|----------|
| 入口 `.py` + lib 变更 | ✅ |
| `scripts/<stage>/README.md` | ✅ |
| `deploy.env.example` 增补变量说明 | 若有新变量则 ✅ |
| 模块或根 `*_WORKFLOW.md` 增订 | 建议 ✅ |
| `--help` 与 docstring | ✅ |
| `config.env.example` | 可选 |

---

## 5. 测试范式（Step 4）

### 5.1 MVP

| 项 | 要求 |
|----|------|
| 规模 | 1 个体系 |
| 命令 | 优先 `--dry-run`，再真实写文件 |
| 检查 | `ls` 期望生成物；打印路径与规格表一致 |
| 失败 | 修脚本或规格，**不进入批量** |

### 5.2 集群系统测

| 项 | 要求 |
|----|------|
| 环境 | 登录节点 `source deploy.env`；`echo $SCRIPTS_ROOT` 非空 |
| 范围 | ≥2 体系或真实队列提交（视任务） |
| 清理 | 提交标记 / 幂等策略验证 |

### 5.3 简易使用卡模板

```markdown
# <模块>/<阶段> 一页卡

## 加载
source <path>/deploy.env
echo SCR=[$SCRIPTS_ROOT] WR=[$WORK_ROOT]

## 命令（复制即用）
$PY $SCR/... 
$PY $SCR/...

## 成功标志
ls <期望文件>

## 若失败
- SCR 空 → 先 source
- 文件找不到 → 对规格表看阶段是否跳步
```

### 5.4 详细手册

可直接采用阶段 README + WORKFLOW 交叉链接；补充集群特有：队列名、模块 load、赝势路径。

### 5.5 上手文档三层结构（强制交付顺序）

每个可运行模块在**主目录或模块入口**须提供「快速上手」类文档，**章节顺序固定**：

| 层 | 章节 | 读者 | 内容 |
|----|------|------|------|
| **①** | MVP 计算流程 | 首次接触 | 1 体系、最少命令、成功标志、3 条故障 |
| **②** | 高通量计算流程 | 日常批量 | `--scan` / batch 入口、幂等、默认是否出图 |
| **③** | 分脚本单独运行 | 调试单步 | 每入口：命令、输入、生成物、不生成 |

> **黄金落地样例**：  
> - VASP：仓库根 [`VASP_QUICKSTART.md`](VASP_QUICKSTART.md)  
> - AIMD：仓库根 [`AIMD_QUICKSTART.md`](AIMD_QUICKSTART.md)

模板骨架：

```markdown
# <模块> 快速上手（MVP → 高通量 → 分脚本）

## 0. 30 秒概念（路径两类 + 关键变量）
## 1. MVP 计算流程
## 2. 高通量计算流程
## 3. 分脚本单独运行流程
## 4. 脚本信息速查表
## 5. 文档导航（链回本范式 / WORKFLOW / SPEC）
```

---

## 6. Agent 回答范式（查现有脚本时）

```
【路径说明】
【当前阶段】
【推荐命令】
【本步生成物】表：文件 | 路径 | 生成者
【下一步】
【前置条件】
【关联脚本】
```

完整示例见 `VASP_WORKFLOW.md` §7；日常命令优先给 `VASP_QUICKSTART.md` / `AIMD_QUICKSTART.md`。

---

## 7. 与现有模块对照（黄金样例）

### 7.1 VASP

| 范式项 | VASP 落点 |
|--------|-----------|
| **上手三层** | **`VASP_QUICKSTART.md`（主目录）** |
| deploy | `vasp/deploy.env.example` |
| lib | `vasp/scripts/lib/{bootstrap,path_config,vasp_common,scf_common}.py` |
| stage README | `vasp/scripts/opt/README.md` 等 |
| 全量 WORKFLOW | `VASP_WORKFLOW.md` |
| 回答范式 | §7 |
| 已知坑 | `make_potcar` 曾误传 `keep_single`；`$VASP_SCRIPTS_ROOT` 空 → `/opt/*.py` |

### 7.2 AIMD（后处理 · 已对齐）

| 范式项 | AIMD 落点 |
|--------|-----------|
| **上手三层** | **`AIMD_QUICKSTART.md`（主目录）** |
| deploy | `AIMD/deploy.env.example`（`AIMD_*`，与 VASP 分离） |
| lib / stage | `AIMD/scripts/lib/`、`AIMD/scripts/MSD_RMSD/` |
| WORKFLOW / SPEC | `AIMD/AIMD_WORKFLOW.md`、`AIMD/AIMD_DEPLOY_SPEC.md` |
| 数据布局 | `$AIMD_WORK_ROOT/<A>/{opt,scf-MD,AIMD}/` + 汇总 `MSD_data_for_origin` / `MSD_png` |
| dt | 各体系 `AIMD/INCAR`→`POTIM`（禁止静态默认顶替） |

新建阶段应复制本结构，而不是另起一套命名。

---

## 8. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-07-14 | 初版：从 high-317 部署踩坑 + scripts/README/WORKFLOW 蒸馏 |
| 2026-07-14 | 增 §5.5 上手三层；纳入 AIMD_QUICKSTART 为落地样例 |
| 2026-07-14 | 增 VASP_QUICKSTART.md，与 AIMD 上手文档同构 |
