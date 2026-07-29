#!/usr/bin/env python3
"""测试 MSD 公共模块的轨迹读取与周期边界处理。

基本用法:
  python3 -m unittest AIMD/tests/test_msd_common.py

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


class ReadXdatcarTests(unittest.TestCase):
    """验证 XDATCAR 坐标在进入 MSD 计算前正确展开。"""

    def test_unwraps_direct_coordinates_across_periodic_boundary(self) -> None:
        content = """Periodic crossing
1.0
10.0 0.0 0.0
0.0 10.0 0.0
0.0 0.0 10.0
H
1
Direct configuration=     1
0.950000 0.100000 0.100000
Direct configuration=     2
0.020000 0.100000 0.100000
Direct configuration=     3
0.080000 0.100000 0.100000
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xdatcar = Path(tmpdir) / "XDATCAR"
            xdatcar.write_text(content, encoding="utf-8")
            positions, elem_map = read_xdatcar(xdatcar)

        np.testing.assert_allclose(positions[:, 0, 0], [9.5, 10.2, 10.8])
        results = compute_msd_by_element(positions, 1.0, elem_map)
        np.testing.assert_allclose(results["H"][1], [0.0, 0.49, 1.69])


if __name__ == "__main__":
    unittest.main()
