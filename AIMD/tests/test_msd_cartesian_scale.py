#!/usr/bin/env python3
"""测试 Cartesian XDATCAR 的全局缩放因子。

基本用法:
  python3 -m unittest AIMD/tests/test_msd_cartesian_scale.py

参数:
  无。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import compute_msd_by_element, read_xdatcar


class CartesianScaleTests(unittest.TestCase):
    """验证 Cartesian 坐标按 VASP 全局因子缩放后再计算 MSD。"""

    def test_applies_scale_to_cartesian_positions(self) -> None:
        content = """Scaled Cartesian trajectory
2.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H
1
Cartesian configuration=     1
0.25 0.0 0.0
Cartesian configuration=     2
0.75 0.0 0.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xdatcar = Path(tmpdir) / "XDATCAR"
            xdatcar.write_text(content, encoding="utf-8")
            positions, elem_map = read_xdatcar(xdatcar)

        np.testing.assert_allclose(positions[:, 0, 0], [0.5, 1.5])
        results = compute_msd_by_element(positions, 1.0, elem_map)
        np.testing.assert_allclose(results["H"][1], [0.0, 1.0])


if __name__ == "__main__":
    unittest.main()
