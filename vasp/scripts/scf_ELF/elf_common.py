#!/usr/bin/env python3
"""
elf_common.py — 向后兼容模块（已重构，此文件导入新模块）

功能已拆分至 scripts/lib/vasp_common.py 与 scripts/lib/scf_common.py。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from bootstrap import init_imports

init_imports()

from vasp_common import *  # noqa: F403, E402
from scf_common import SCF_INCAR  # noqa: E402
