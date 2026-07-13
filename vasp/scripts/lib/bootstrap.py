"""脚本包导入引导：与计算工作目录无关，仅定位 scripts/ 安装根。"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parent.parent


def init_imports() -> Path:
    """将 lib / opt / scf_ELF 加入 sys.path，并可选加载 deploy.env。"""
    from path_config import load_deploy_env, scripts_root

    load_deploy_env()
    root = scripts_root()
    for sub in ("lib", "opt", "scf_ELF"):
        path = str(root / sub)
        if path not in sys.path:
            sys.path.insert(0, path)
    return root
