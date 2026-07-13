# lib — AIMD 公共库

| 文件 | 职责 |
|------|------|
| `bootstrap.py` | import 路径 + 加载 `AIMD_DEPLOY_ENV` |
| `path_config.py` | `AIMD_SCRIPTS_ROOT` / `AIMD_WORK_ROOT` / `--work-root` |
| `msd_common.py` | XDATCAR、MSD、POTIM、汇总 `mv` |

路径优先级：`--work-root` > `$AIMD_WORK_ROOT` > cwd。
