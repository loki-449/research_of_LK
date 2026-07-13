# calculation — 高通量计算脚本工作区

凝聚态 DFT 辅助脚本集（VASP / QE / AIMD）。  
**每次开始新工作前，必须走下方「强制流程」**——对话先定流程，再批判修订，最后才写代码与测试。

---

## 强制工作流（对话 → 部署 → 测试）

> Agent 与人工均须遵守。对应 Cursor 技能：`.cursor/skills/calc-script-deploy/`。

### Step 1 — 询问并确认大体流程

1. 用户用对话说明目标（例如「部署 opt」「加 Bader 阶段」）。
2. Agent **拆解逻辑**，给出 3–8 步草案，并**主动询问**：  
   「请确认大体工作流程是否如下？」
3. **用户确认前：不写脚本、不改目录结构。**

### Step 2 — 批判性审查并定稿

1. 在已确认草案上，Agent **批判性指出**可能问题与遗漏（路径混淆、缺前置产物、环境变量、参数名不一致、生成物缺口等）。
2. 双方讨论修订。
3. **修订后的流程 = 唯一执行基准**，写入当次会话纪要或模块 WORKFLOW。

### Step 3 — 脚本部署：先规格、后编码

若任务是**脚本部署**，编码前必须按 [`SCRIPT_DEPLOY_PARADIGM.md`](SCRIPT_DEPLOY_PARADIGM.md) 填齐：

| 必须明确 | 说明 |
|----------|------|
| 案例模板数据 | 最小 MVP 输入（1 个体系 / 1 份 relax.in 等） |
| 逻辑链条 | 输入 → 脚本 → 生成物路径 |
| 脚本功能 | 每个入口做什么 / 不做什么 |
| 参数与变量 | CLI、`deploy.env`、与 `--help` 一致 |
| 路径 | 脚本安装根 vs 计算工作根（两类路径分离） |
| 生成数据 | 文件名 + `$WORK_ROOT/...` 路径模式 |
| 逻辑漏洞 | 批判清单勾选后再动手 |

然后再生成/修改脚本，并同步：

- `scripts/**/README.md`
- `--help` / docstring「基本用法」
- 模块 `*_WORKFLOW.md`（如有）

### Step 4 — MVP → 集群系统测 + 手册

1. **MVP**：单体系、最少依赖、优先 `--dry-run`，确认生成物路径正确。  
2. **集群系统测**：真实 `qsub` / 批量扫描；准备两层手册：  
   - **简易使用卡**（一页可复制命令）  
   - **详细说明**（参数、产物、故障排查）  
3. 手册写法见范式文档 §手册。

---

## 文档与技能索引

| 文档 | 用途 |
|------|------|
| [SCRIPT_DEPLOY_PARADIGM.md](SCRIPT_DEPLOY_PARADIGM.md) | **0. 脚本部署内容范式**（规格表、README/WORKFLOW、**上手三层**模板） |
| [VASP_QUICKSTART.md](VASP_QUICKSTART.md) | **VASP 快速上手**：MVP → 高通量 → 分脚本（日常首选） |
| [AIMD_QUICKSTART.md](AIMD_QUICKSTART.md) | **AIMD 快速上手**：MVP → 高通量 → 分脚本（日常首选） |
| [VASP_WORKFLOW.md](VASP_WORKFLOW.md) | VASP 全脚本用法 · 生成物 · 回答范式 |
| [AIMD/AIMD_WORKFLOW.md](AIMD/AIMD_WORKFLOW.md) | AIMD 详细工作流 / 回答范式 |
| [CLAUDE.md](CLAUDE.md) | Agent 全局路由与代码规范 |
| [CLAUDE_TEMPLATE.md](CLAUDE_TEMPLATE.md) | 新建模块 CLAUDE.md 模板 |
| [vasp/README.md](vasp/README.md) | VASP 模块部署入口 |
| [vasp/deploy.env.example](vasp/deploy.env.example) | VASP 环境变量模板 |
| [AIMD/deploy.env.example](AIMD/deploy.env.example) | AIMD 环境变量模板 |
| `.cursor/skills/calc-script-deploy/` | Cursor 自动加载的部署技能 |

---

## 子模块

| 模块 | 入口 | 说明 |
|------|------|------|
| **VASP** | [vasp/](vasp/) | opt → scf_ELF；**先读** [VASP_QUICKSTART.md](VASP_QUICKSTART.md) |
| **AIMD** | [AIMD/](AIMD/) | MSD/RMSD；**先读** [AIMD_QUICKSTART.md](AIMD_QUICKSTART.md) |

### VASP 两类路径（必读）

| 类型 | 示例 | 说明 |
|------|------|------|
| 脚本包 | `$VASP_SCRIPTS_ROOT` → `vasp/scripts/` | 可拷贝安装，不含计算数据 |
| 计算数据 | `$VASP_WORK_ROOT/<材料>/<压强>/opt\|scf_ELF/` | 运行时生成 |

详细命令见 [VASP_WORKFLOW.md](VASP_WORKFLOW.md)。

---

## 集群启动（环境优先）

```bash
cd /path/to/vasp
cp deploy.env.example deploy.env   # 按本机路径改
source deploy.env
echo "SCR=[$VASP_SCRIPTS_ROOT]"    # 必须非空，否则 python3 /opt/xxx.py 报错

$VASP_PYTHON $VASP_SCRIPTS_ROOT/opt/setup_opt_workflow.py $QE_ROOT
# …后续见 VASP_WORKFLOW.md §5
```

---

## 新人 / Agent 检查清单

- [ ] 已读本 README 强制四步  
- [ ] 已区分脚本路径与工作路径  
- [ ] 已 `source deploy.env` 且 `echo $VASP_SCRIPTS_ROOT` 非空  
- [ ] 写代码前规格表已填（范式文档）  
- [ ] MVP 通过后再做集群批量  
- [ ] 交付了简易卡 + 详细手册（或更新了既有 README）
