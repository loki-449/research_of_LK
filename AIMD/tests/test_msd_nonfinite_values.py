#!/usr/bin/env python3
"""
测试 XDATCAR 非有限数值校验。

用途:
  验证轨迹中的 NaN/Inf 不会进入 MSD 计算或汇总结果。

基本用法:
  python3 -m unittest AIMD/tests/test_msd_nonfinite_values.py

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import read_xdatcar


class NonFiniteXdatcarTests(unittest.TestCase):
    """验证非有限坐标会在读取阶段被拒绝。"""

    def test_rejects_nonfinite_coordinates(self) -> None:
        template = """Non-finite trajectory
1.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H
1
Direct configuration=     1
0.0 0.0 0.0
Direct configuration=     2
{value} 0.0 0.0
"""
        for value in ("nan", "inf", "-inf"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmpdir:
                xdatcar = Path(tmpdir) / "XDATCAR"
                xdatcar.write_text(template.format(value=value), encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "Non-finite coordinates"):
                    read_xdatcar(xdatcar)


if __name__ == "__main__":
    unittest.main()
