#!/usr/bin/env python3
"""
验证 XDATCAR 的三个笛卡尔方向缩放因子可被正确解析。

基本用法:
  python3 -m unittest tests/test_aimd_three_scale_factors.py

参数说明:
  本测试无需命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / "AIMD" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import compute_msd_by_element, read_xdatcar


class ThreeScaleFactorsXdatcarTest(unittest.TestCase):
    """覆盖 VASP 合法的三缩放因子 XDATCAR 头部。"""

    def test_scales_each_cartesian_direction(self) -> None:
        xdatcar_text = """three-factor scale
2.0 3.0 4.0
1.0 1.0 0.0
0.0 1.0 1.0
1.0 0.0 1.0
H
1
Direct configuration= 1
0.0 0.0 0.0
Direct configuration= 2
0.5 0.0 0.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xdatcar = Path(tmpdir) / "XDATCAR"
            xdatcar.write_text(xdatcar_text, encoding="utf-8")

            positions, elements = read_xdatcar(xdatcar)

        np.testing.assert_allclose(positions[1, 0], [1.0, 1.5, 0.0])
        results = compute_msd_by_element(positions, 1.0, elements)
        self.assertAlmostEqual(results["H"][1][1], 3.25)


if __name__ == "__main__":
    unittest.main()
