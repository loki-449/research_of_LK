#!/usr/bin/env python3
"""
test_vasp_common.py — VASP 公共模块回归测试。

用途:
  验证 QE 体系目录名中的材料、压强和温度解析不会混淆化学计量数字。

基本用法:
  python -m unittest discover -s vasp/tests -v

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vasp_common import parse_system_name  # noqa: E402


class ParseSystemNameTests(unittest.TestCase):
    """验证 QE 体系目录名解析。"""

    def test_parses_documented_name(self) -> None:
        self.assertEqual(
            parse_system_name("Ag-H-50GPa-300K"),
            ("Ag", "50", "300"),
        )

    def test_ignores_stoichiometric_digits_before_pressure(self) -> None:
        self.assertEqual(
            parse_system_name("Ag-H2-50GPa-300K"),
            ("Ag", "50", "300"),
        )

    def test_parses_decimal_pressure_after_stoichiometry(self) -> None:
        self.assertEqual(
            parse_system_name("Fe-O2-12.5GPa-500K"),
            ("Fe", "12.5", "500"),
        )

    def test_rejects_name_without_gpa_pressure(self) -> None:
        self.assertIsNone(parse_system_name("Ag-H2-300K"))


if __name__ == "__main__":
    unittest.main()
