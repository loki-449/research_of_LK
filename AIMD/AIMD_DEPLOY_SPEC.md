# AIMD 规范化部署 — Step 3 规格表（待确认 · 未改代码）

> 状态：**规格已落地编码**（2026-07-14）。MVP 用 `example/demo/` 已冒烟通过。  
> 用户若提供完整 XDATCAR，可替换/增删 `example/` 后再测。

---

## 3.1 元信息

| 项 | 填写 |
|----|------|
| 模块名 | AIMD |
| 子阶段（本轮） | MSD/RMSD 后处理（`MSD_RMSD`） |
| 脚本安装根变量 | `AIMD_SCRIPTS_ROOT` |
| 计算工作根变量 | `AIMD_WORK_ROOT` |
| 输入约定 | `$AIMD_WORK_ROOT/<A>/AIMD/XDATCAR` + 同目录 `INCAR`（读 POTIM） |
| deploy 配置 | `AIMD/deploy.env.example` → `deploy.env`（**与 vasp/deploy.env 分开**） |
| 自动加载 | `AIMD_DEPLOY_ENV` |
| Python | `AIMD_PYTHON`（默认 `python3`） |
| 依赖 | `numpy`（提取）；`matplotlib`（绘图） |

---

## 3.2 路径三类

| 类型 | 典型路径 | 可否删 |
|------|----------|--------|
| **脚本包** | `$AIMD_SCRIPTS_ROOT/` ← `AIMD/scripts/` | ❌ |
| **计算数据** | `$AIMD_WORK_ROOT/<A>/{opt,scf-MD,AIMD}/` | 有数据勿删 |
| **产物汇总** | `$AIMD_WORK_ROOT/MSD_data_for_origin/`、`$AIMD_WORK_ROOT/MSD_png/` | 勿删结果 |
| **示例** | `AIMD/example/`（仓库内，供 MVP） | ❌ |
| **遗留** | `AIMD/MSD&RMSD/` | 迁移后留跳转 README |

### 数据目录树（定稿）

```
$AIMD_WORK_ROOT/
├── MSD_data_for_origin/     # ★ 汇总 .dat（由脚本 mkdir + mv 写入）
│   └── <A>_msd_data.dat     # 自 <A>/msd_data.dat 挪入并改名，避免互撞
├── MSD_png/                 # ★ 汇总 png
│   └── <A>_msd_rmsd.png
└── <A>/                     # 体系
    ├── opt/                 # 本轮 MSD 不读
    ├── scf-MD/              # 本轮 MSD 不读
    ├── AIMD/
    │   ├── XDATCAR          # ★ 输入
    │   └── INCAR            # ★ 解析 POTIM → dt（fs）
    └── msd_data.dat         # ★ 中间输出（extract 写这里），成功后 mv 走
```

**产物流转（强制 `mv`，避免体系目录堆文件）：**

```
写文件:  $WR/<A>/msd_data.dat
         $WR/<A>/<临时>.png     （若出图）
    │
    └─ mv →  $WR/MSD_data_for_origin/<A>_msd_data.dat
             $WR/MSD_png/<A>_msd_rmsd.png
```

> 中间文件用固定名 `msd_data.dat` 落在 **体系根 `<A>/`**（不是 `AIMD/` 内）。  
> 汇总目录内必须带 `<A>_` 前缀，否则多体系 `mv` 会互相覆盖。

批量扫描：`$AIMD_WORK_ROOT/*/AIMD/XDATCAR`（跳过名为 `MSD_data_for_origin`、`MSD_png` 的非体系目录）。

### 脚本包 + example 目标树

```
AIMD/
├── deploy.env.example
├── README.md
├── CLAUDE.md
├── AIMD_WORKFLOW.md
├── AIMD_DEPLOY_SPEC.md          # 本文件
├── example/                     # ★ MVP 示例（用户稍后提供 XDATCAR）
│   ├── README.md                # 说明如何裁剪帧数 / 最小集合
│   ├── <A>/                     # 例：demo_system/
│   │   └── AIMD/
│   │       ├── XDATCAR          # 可删减帧，求最快跑通
│   │       └── INCAR            # 至少含 POTIM=...
│   └── （可选）裁剪脚本说明
└── scripts/
    ├── install.sh
    ├── README.md
    ├── lib/
    │   ├── bootstrap.py
    │   ├── path_config.py
    │   ├── msd_common.py        # + read_potim_from_incar / resolve_dt
    │   └── ...
    ├── MSD_RMSD/
    │   ├── extract_msd_flex.py
    │   ├── plot_msd_flex.py
    │   ├── xdatcar_msd_flex.py
    │   ├── plot_line_template.py
    │   ├── run_msd_batch.py
    │   └── README.md
    └── compat/
        └── ...
```

---

## 3.3 案例模板数据（MVP）

| 项 | 值 |
|----|-----|
| 位置 | `AIMD/example/<A>/AIMD/` |
| 输入 | 用户提供的 `XDATCAR` + `INCAR`（含 `POTIM`） |
| 裁剪原则 | 保留文件头 + **尽量少的帧**（如 20–50 帧）以最快跑通；从完整轨迹删减，不改元素行 |
| `--dt` | **禁止手填默认顶替**；从该体系 `INCAR` 的 `POTIM` 读取 |
| 期望 | `$WR/<A>/msd_data.dat` → `mv` → `$WR/MSD_data_for_origin/<A>_msd_data.dat` |
| 成功判据 | 汇总目录存在非空 `.dat`；header 含 `Time(ps)` 与 `*_MSD(A2)` |

测试时可设 `AIMD_WORK_ROOT` 指向临时目录，并把 `example/<A>` 链/拷进去。

---

## 3.4 逻辑链条

```
$WR/<A>/AIMD/{XDATCAR, INCAR}
        │
        ├─ resolve_dt(INCAR) → POTIM (fs)
        │
        ├─[extract]──→ $WR/<A>/msd_data.dat
        │                    │
        │                    └─ mv → $WR/MSD_data_for_origin/<A>_msd_data.dat
        │
        └─[--with-plot]──→ 临时 png @ <A>/
                               └─ mv → $WR/MSD_png/<A>_msd_rmsd.png
```

启动批量前：`mkdir -p $WR/MSD_data_for_origin $WR/MSD_png`。

---

## 3.5 环境变量（独立 deploy.env）

| 变量 | 含义 | 示例 |
|------|------|------|
| `AIMD_SCRIPTS_ROOT` | 脚本安装根 | `.../AIMD/scripts` |
| `AIMD_WORK_ROOT` | AIMD **数据**根 | `.../aimd_work` |
| `AIMD_PYTHON` | 解释器 | `python3` |
| `AIMD_DEPLOY_ENV` | deploy.env 路径 | `.../AIMD/deploy.env` |

### 关于 `AIMD_DT_DEFAULT`（重要修订）

| 原设想 | **废止**作为静态 `export AIMD_DT_DEFAULT=1.0` |
|--------|-----------------------------------------------|
| **正确定义** | **不是**写死在 deploy.env 的常数；对每个体系运行时从 **`$AIMD_WORK_ROOT/<A>/AIMD/INCAR`** 解析 `POTIM` |
| 优先级 | CLI `--dt`（显式） > INCAR `POTIM` > （仅当二者皆无）报错退出，**不静默用 1.0** |
| 路径澄清 | INCAR 在**工作数据根**下，**不在** `AIMD_SCRIPTS_ROOT`。若口误说 scripts，规格一律按 WORK_ROOT 实现 |

#### `dt` / INCAR 参数与结果关系（文档必写备注）

| 参数 | 含义 | 对 MSD/RMSD 的影响 |
|------|------|-------------------|
| **POTIM** | AIMD 时间步长（fs） | **直接决定** 横轴 `Time(ps)=frame_index*POTIM/1000`。错读会整体拉伸/压缩时间轴，扩散斜率（扩散系数估计）成比例错误 |
| NSW | 离子步数 | 影响轨迹长度（帧数）；不进公式，但决定统计是否够 |
| SMASS / 系综相关 | 热浴等 | 不改本脚本公式；影响物理轨迹本身 |
| TEBEG/TEEND | 温度 | 不改脚本；不同 T 的 MSD 斜率不同（物理） |
| POMASS 等 | 质量 | 不进入当前几何 MSD 实现 |
| 输出相关 LWAVE 等 | I/O | 与 MSD 后处理无关 |

脚本应在日志打印：`dt=... fs (from INCAR POTIM at .../AIMD/INCAR)`，便于核对。

可选：deploy.env 注释中保留说明段，**不**导出错误默认值。

---

## 3.6 单脚本规格卡（增量修订）

### A. `lib/msd_common.py`

| 新增 API | 说明 |
|----------|------|
| `iter_aimd_xdatcars(work_root)` | `*/AIMD/XDATCAR`，排除汇总目录名 |
| `read_potim_from_incar(incar_path) -> float` | 解析 `POTIM`；缺失则抛错 |
| `resolve_dt(aimd_dir, cli_dt=None) -> float` | CLI > POTIM > 报错 |
| `ensure_result_dirs(work_root)` | `mkdir` `MSD_data_for_origin`、`MSD_png` |
| `publish_dat(src_dat, work_root, system_A)` | `mv` → `MSD_data_for_origin/<A>_msd_data.dat` |
| `publish_png(src_png, work_root, system_A)` | `mv` → `MSD_png/<A>_msd_rmsd.png` |

### C. `extract_msd_flex.py`

| 项 | 内容 |
|----|------|
| 默认输出 | `$WR/<A>/msd_data.dat`（由 XDATCAR 路径反推 `<A>=.../AIMD` 的父目录） |
| 完成后 | 默认 **`mv` 到汇总目录**；可选 `--keep-local` 保留体系下副本（默认不保留，贯彻少文件） |
| `--dt` | 可选覆盖；未给则读同体系 `AIMD/INCAR` |
| `--scan` / batch | 见 G |

### D / E. 绘图

| 项 | 内容 |
|----|------|
| 读入 | 优先 `$WR/MSD_data_for_origin/<A>_msd_data.dat`；兼容未 mv 的 `$WR/<A>/msd_data.dat` |
| 写图 | 先写临时路径再 `mv` 到 `MSD_png/<A>_msd_rmsd.png` |
| 批量 | 默认 **不出图**；`--with-plot` 才画 |

### G. `run_msd_batch.py`

| 项 | 内容 |
|----|------|
| 启动 | `ensure_result_dirs` |
| 每体系 | resolve_dt → extract → `msd_data.dat` → `publish_dat` |
| 默认文件名 | 中间：`<A>/msd_data.dat`；汇总：`<A>_msd_data.dat` |
| `--with-plot` | 可选；png 同样 `mv` 汇总 |
| `--dry-run` | 只打印 XDATCAR、POTIM、目标 mv 路径 |

### example/

| 项 | 内容 |
|----|------|
| 建立 | `AIMD/example/` + README（如何放 XDATCAR、如何删减帧） |
| 内容 | 用户稍后提供；可提取关键头信息后大幅删帧做 MVP |

---

## 3.7 本轮边界（更新）

| 做 | 不做 |
|----|------|
| 路径重构、`bootstrap`、独立 deploy | 改 MSD 物理公式 |
| INCAR→POTIM 自动 dt | 把 INCAR 放到 scripts 树下 |
| 中间 `<A>/msd_data.dat` + **mv** 汇总 | 在每个 `AIMD/` 内堆大量结果文件 |
| `example/` 最小样例 | 本轮部署 opt/scf-MD 计算链 |

---

## 3.8 批判清单（增补）

- [x] `dt` 来源：WORK_ROOT 下 INCAR，非 SCRIPTS_ROOT
- [x] 汇总目录 + `mv`，汇总文件带 `<A>_` 前缀防覆盖
- [ ] 批量扫描必须 **跳过** `MSD_data_for_origin`、`MSD_png`（以及 `example` 若挂在 WR 下）
- [ ] Windows 开发机无真正 `mv` 时用 `Path.replace`/`shutil.move` 等价实现
- [ ] INCAR 缺 POTIM / 写在 `.INCAR` 副本：明确报错信息
- [ ] 用户若手动 `--dt` 与 INCAR 不一致：日志 **警告** 但不拦截（显式优先）
- [ ] example 中超大 XDATCAR：文档要求删减后再 commit

---

## 3.9 文档交付清单

同前，外加：

| 文档 | 必须写清 |
|------|----------|
| WORKFLOW / README | 产物流转图；POTIM↔Time 关系表 |
| `example/README.md` | 样例布局、删帧指引、MVP 命令 |
| deploy.env.example | **不**设置静态 `AIMD_DT_DEFAULT=1.0`；改为注释说明「dt 从各体系 INCAR 读取」 |

---

## 3.10 推荐命令（预览）

```bash
source /path/to/AIMD/deploy.env
mkdir -p "$AIMD_WORK_ROOT"   # 首次；汇总目录可由脚本自动建

# 单体系（dt 自动自 INCAR）
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py \
  "$AIMD_WORK_ROOT/Ba3AgH7/AIMD/XDATCAR"
# → 写 Ba3AgH7/msd_data.dat → mv → MSD_data_for_origin/Ba3AgH7_msd_data.dat

# 批量
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py
$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/run_msd_batch.py --with-plot

# MVP（示例）：AIMD_WORK_ROOT 指到 example 的父数据布局后同上
```

---

## 3.11 小项决议（修订后）

| # | 问题 | 决议 |
|---|------|------|
| 1 | 中间 .dat 路径 | ✅ `$WR/<A>/msd_data.dat` |
| 2 | 最终 .dat 位置 | ✅ `mv` → `$WR/MSD_data_for_origin/<A>_msd_data.dat` |
| 3 | png | ✅ `mv` → `$WR/MSD_png/<A>_msd_rmsd.png`；批量默认不出图 |
| 4 | `AIMD_DT_DEFAULT` | ✅ **取消静态默认**；每体系读 `$WR/<A>/AIMD/INCAR` 的 `POTIM` |
| 5 | example | ✅ 建 `AIMD/example/`；等用户给 XDATCAR 后删减跑通 |
| 6 | 旧 `MSD&RMSD/` | 跳转 README 后择机删 |

---

确认本修订规格后回复「按规格开改」→ 编码 + 文档；example 内真实 XDATCAR 可随后再发。
