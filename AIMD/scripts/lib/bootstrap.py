"""AIMD 脚本包导入引导：与计算工作目录无关，仅定位 scripts/ 安装根。"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parent.parent


def init_imports() -> Path:
    """将 lib / MSD_RMSD 加入 sys.path，并可选加载 deploy.env。"""
    from path_config import load_deploy_env, scripts_root

    load_deploy_env()
    root = scripts_root()
    if root != SCRIPTS_ROOT:
        raise RuntimeError(
            "AIMD_SCRIPTS_ROOT 与当前入口脚本不属于同一安装目录："
            f"配置为 {root}，当前为 {SCRIPTS_ROOT}。"
            "请更新环境变量或改用配置目录中的入口脚本，避免混用不同版本。"
        )
    for sub in ("lib", "MSD_RMSD"):
        path = str(root / sub)
        if path not in sys.path:
            sys.path.insert(0, path)
    return root
