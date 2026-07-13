---
name: calc-script-deploy
description: >-
  Guides high-throughput DFT calculation script deployment for this repo
  (VASP/QE/AIMD). Enforces ask-workflow → critique → finalize → code → MVP →
  cluster test. Use when deploying scripts, writing README/WORKFLOW docs,
  creating opt/scf_ELF pipelines, or when the user mentions 脚本部署, 工作流,
  deploy.env, VASP_WORKFLOW, or 新模块脚本.
---

# 计算脚本部署技能

本技能绑定仓库 `calculation/`。**每次新任务必须先走强制对话流程，禁止跳过直接写代码。**

完整范式与模板见 [paradigm.md](paradigm.md)。权威脚本说明见仓库根 `VASP_WORKFLOW.md`、`README.md`。  
AIMD 日常上手优先读仓库根 **`AIMD_QUICKSTART.md`**；VASP 优先读 **`VASP_QUICKSTART.md`**（均为 MVP → 高通量 → 分脚本）。该结构已写入 `SCRIPT_DEPLOY_PARADIGM.md` §5.5。

## 强制四步流程（不可跳过）

复制进度表并跟踪：

```
任务进度:
- [ ] Step 1 询问并拆解 → 确认大体工作流程
- [ ] Step 2 批判性审查 → 指出漏洞/遗漏 → 修订流程
- [ ] Step 3 若为脚本部署 → 按范式填规格表 → 再写代码
- [ ] Step 4 MVP 测试 → 再出集群简易/详细手册
```

### Step 1：询问工作流程

用户提出目标后：

1. 用中文拆解意图（计算阶段、输入来源、输出产物、运行环境）。
2. **先问**：「请确认大体工作流程是否如下？」并给出 3–8 步草案。
3. **禁止**在用户确认前写脚本或改目录结构。

### Step 2：批判性审查

用户确认草案后，主动指出：

| 检查项 | 典型问题 |
|--------|----------|
| 路径混淆 | 脚本目录 vs 工作数据目录 vs 遗留空目录 |
| 顺序依赖 | 下游是否误用不存在的上游产物（如无 CONTCAR 就做 scf） |
| 环境变量 | `source deploy.env` 是否被漏掉；shell 展开 vs Python 内部加载 |
| 参数一致性 | argparse 实参名与公共库函数形参是否一致（如 `keep_single` vs `keep_single_files`） |
| 生成物缺口 | PBS / POSCAR / POTCAR / 提交标记谁写、谁不写 |
| 可移植性 | 硬编码绝对路径、第三方依赖、PBS 模块名 |

列出问题 → 与用户讨论 → **修订后的流程成为唯一执行基准**。

### Step 3：脚本部署规格（写代码前）

若确认为脚本部署，按 [paradigm.md](paradigm.md) 填齐规格表后再编码。最少覆盖：

- 案例模板数据（最小 MVP 输入）
- 逻辑链条（输入 → 脚本 → 生成物路径）
- 每脚本：功能、CLI 参数、环境变量、生成物、不生成物
- 批判：仍可能存在的逻辑漏洞

**代码约定（与仓库一致）：**

- Python 3.8+ 标准库；`bootstrap.init_imports()`；`--work-root` > `$WORK_ROOT` > cwd
- 脚本包与计算数据路径分离；分步优先于一键
- README / `--help` / WORKFLOW 文档三者一致
- 新增公共 API 放入 `scripts/lib/` 的 `_common` 模块

### Step 4：测试与手册

1. **MVP**：单体系、最少文件、本地或登录节点 dry-run 跑通。
2. **集群**：再批量；交付两层手册（简易卡 + 详细页）。模板见 paradigm.md §手册。

## 回答范式（对用户说明脚本时）

对齐 `VASP_WORKFLOW.md` §7：

```
【路径说明】脚本在…；数据在…；勿混淆遗留目录
【当前阶段】opt / scf_ELF / 环境部署 / …
【推荐命令】带环境变量的可复制命令
【本步生成物】文件 | 路径 | 生成者
【下一步】产物 → 下一脚本 → 下一产物
【前置条件】
【关联脚本】等价于 / 依赖 / 被谁调用
```

## 关键决策

| 场景 | 动作 |
|------|------|
| 用户问「某某脚本怎么用」 | 按上述回答范式 + 读对应 README / WORKFLOW |
| 用户问是否删目录 | 区分脚本包 / 遗留空目录 / 工作数据目录 |
| `$SCRIPTS_ROOT` 空导致 `/opt/xxx.py` | 未 `source deploy.env`；先修环境再跑脚本 |
| 新模块（非 VASP） | 仍走四步；文档结构仿 `vasp/scripts/*/README.md` |

## 参考索引

| 文档 | 用途 |
|------|------|
| [paradigm.md](paradigm.md) | 规格表、README 模板、手册模板 |
| `README.md`（仓库根） | 强制流程的用户向说明 |
| `SCRIPT_DEPLOY_PARADIGM.md` §5.5 | 上手三层（MVP→高通量→分脚本） |
| `VASP_QUICKSTART.md` | VASP 上手落地样例 |
| `AIMD_QUICKSTART.md` | AIMD 上手落地样例 |
| `VASP_WORKFLOW.md` | VASP 全脚本用法与路径 |
| `vasp/CLAUDE.md` / `AIMD/CLAUDE.md` | 模块路由 |
