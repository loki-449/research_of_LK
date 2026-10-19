"""
_forward.py — 历史 AIMD 入口到规范脚本包的兼容转发。

用途:
  让 AIMD/MSD&RMSD 下保留的旧命令执行 AIMD/scripts/MSD_RMSD
  中的当前实现，避免旧副本继续产生与规范工作流不一致的结果。

基本用法:
  由同目录兼容入口调用，不直接运行。

参数说明:
  script_name: AIMD/scripts/MSD_RMSD 下的目标脚本文件名。
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def forward(script_name: str) -> None:
    """以原命令行参数执行规范入口，并保留其退出码。"""
    target = Path(__file__).resolve().parents[1] / "scripts" / "MSD_RMSD" / script_name
    if not target.is_file():
        raise FileNotFoundError(f"规范 AIMD 入口不存在: {target}")

    print(
        f"WARNING: {Path(sys.argv[0]).parent} 为历史路径，"
        f"正在转发到 {target}",
        file=sys.stderr,
    )
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
