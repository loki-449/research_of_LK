# 本项目下对话使用中文

# 项目定位
- 凝聚态物理第一性原理（DFT）理论计算辅助脚本集
- 计算引擎：VASP（大规模并行）、Quantum ESPRESSO（QE，结构优化前处理）
- 运行环境：Linux HPC 集群（PBS 作业调度，Intel oneAPI + VASP）
- 用户角色：凝聚态物理理论研究者，需要高通量计算部署和后处理能力

# 强制工作流（每次新任务）

**开始任何脚本部署 / 新阶段开发前，必须遵守根 `README.md` 四步：**  
① 询问并确认大体流程 → ② 批判性指出漏洞并修订定稿 → ③ 按 `SCRIPT_DEPLOY_PARADIGM.md` 填规格后再编码 → ④ MVP → 集群测 + 简易/详细手册。  

Cursor 技能：`.cursor/skills/calc-script-deploy/`（含 paradigm.md）。  
**禁止跳过 Step 1–2 直接写代码。**

# 子模块路由（Agent 体系）

当用户需求涉及以下模块时，优先加载对应子目录下的 CLAUDE.md 获取模块级指令：

| 模块 | 文档 | 职责 |
|------|------|------|
| **工作流总则** | `README.md` | 强制四步、文档索引 |
| **脚本部署范式** | `SCRIPT_DEPLOY_PARADIGM.md` | 规格表、README/WORKFLOW/手册模板 |
| **VASP 快速上手** | `VASP_QUICKSTART.md` | MVP → 高通量 → 分脚本（优先） |
| **VASP（大型模块）** | `vasp/CLAUDE.md` | 结构优化（opt）→ ELF 计算（scf_ELF）→ 未来 Bader 分析，统一入口 |
| **VASP 使用说明（回答范式）** | `VASP_WORKFLOW.md` | 全部脚本用法、生成物路径、脚本关联、scf_ELF 三层含义 |
| **AIMD 后处理** | `AIMD/CLAUDE.md` | MSD/RMSD；独立 `AIMD_*` |
| **AIMD 快速上手** | `AIMD_QUICKSTART.md` | MVP → 高通量 → 分脚本（优先） |
| **AIMD 部署规格** | `AIMD/AIMD_DEPLOY_SPEC.md` | 规范化部署规格表 |

# 全局代码规范
- Python 3.8+，仅标准库（无第三方依赖），保持跨服务器可移植
- 脚本命名：snake_case，功能明确的动词_名词格式
- 公共模块以 _common 结尾，可被同级脚本直接 import
- 每个 .py 文件头包含完整 docstring：用途、基本用法、参数说明
- 通过 sys.path 管理模块导入，避免硬编码绝对路径
- 默认路径（赝势库、输出目录）定义为模块级常量，可通过环境变量或命令行参数覆盖

# 全局物理约定
- ENCUT 截断能默认 800 eV（硬赝势体系）
- K 点间距默认 KSPACING=0.03，Gamma 中心网格
- 电子收敛 EDIFF=1e-6
- 赝势库默认路径：/home/test1/hhy/basic/psudopotential/PAW-GGA-PBE
- 赝势择优：ZVAL（价电子数）最大优先；ZVAL 相同时取日期最新

# 全局工作流约定
- 目录建立先于文件部署（mkdir -p 策略），部分失败不删已有文件
- 优先使用分步脚本而非一键脚本，便于调试
- 重构已有代码时保留向后兼容（旧模块改为 import 包装）
- 讨论物理问题时，从物理图像出发，再进入公式细节

# 交互偏好
- 所有回答使用中文
- 代码注释和 docstring 使用中文
- 每次修改完成后自动提交并推送至 GitHub

# Git / GitHub
- 远程仓库: git@github.com:loki-449/research_of_LK.git
- 主分支: master（推送目标）；main 分支为同步镜像
- 每次修改完成后，自动提交并推送至远程仓库
- 每日 9:00 自动推送最新脚本到 master 分支（定时任务: daily-push-to-github）
- 注意：GitHub 默认分支为 main，推送时使用 `git push origin main`，本地按 main 分支操作
