#!/usr/bin/env python3
"""
验证 XDATCAR 负缩放因子按 VASP 的目标晶胞体积语义解析。

基本用法:
  python3 -m unittest AIMD/tests/test_msd_negative_scale.py

参数说明:
  本测试无需命令行参数。
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


class NegativeScaleXdatcarTest(unittest.TestCase):
    """覆盖负缩放因子对应目标体积的轨迹读取与 MSD 计算。"""

    def test_negative_scale_is_interpreted_as_target_volume(self) -> None:
        xdatcar_text = """Negative scale
-8.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
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

        np.testing.assert_allclose(positions[1, 0], [1.0, 0.0, 0.0])
        results = compute_msd_by_element(positions, 1.0, elements)
        self.assertAlmostEqual(results["H"][1][1], 1.0)


if __name__ == "__main__":
    unittest.main()
