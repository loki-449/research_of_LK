#!/usr/bin/env python3
"""
test_msd_common.py — MSD 公共模块回归测试

用途:
  验证 XDATCAR 读取在遇到文件末尾未写完的构型时保留完整帧，
  避免实时/批量后处理因轨迹数组形状不一致而崩溃。

基本用法:
  python -m unittest discover -s AIMD/tests -v

参数:
  无。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import read_xdatcar


class ReadXdatcarTests(unittest.TestCase):
    """验证 XDATCAR 构型完整性处理。"""

    def test_ignores_incomplete_trailing_frame(self) -> None:
        """VASP 尚未写完最后一帧时，仅返回此前的完整帧。"""
        content = """test
1.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H
2
Direct configuration=     1
0.0 0.0 0.0
0.5 0.5 0.5
Direct configuration=     2
0.1 0.0 0.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xdatcar = Path(tmpdir) / "XDATCAR"
            xdatcar.write_text(content, encoding="utf-8")

            positions, elem_map = read_xdatcar(xdatcar)

        self.assertEqual(positions.shape, (1, 2, 3))
        self.assertEqual(elem_map, ["H", "H"])


if __name__ == "__main__":
    unittest.main()
