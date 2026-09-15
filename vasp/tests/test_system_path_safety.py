#!/usr/bin/env python3
"""
验证 QE 体系名不能通过路径分量逃逸 VASP 工作根目录。

基本用法:
  python3 -m unittest vasp/tests/test_system_path_safety.py

参数说明:
  无；测试仅解析体系目录名，不读写真实计算数据。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import parse_system_name


class SystemPathSafetyTests(unittest.TestCase):
    """拒绝会被 pathlib 解释为父级或当前级的路径分量。"""

    def test_parent_material_is_rejected(self) -> None:
        self.assertIsNone(parse_system_name("..-50GPa-300K"))

    def test_current_material_is_rejected(self) -> None:
        self.assertIsNone(parse_system_name(".-50GPa-300K"))

    def test_parent_pressure_is_rejected(self) -> None:
        self.assertIsNone(parse_system_name("Ag-..GPa-300K"))

    def test_current_pressure_is_rejected(self) -> None:
        self.assertIsNone(parse_system_name("Ag-.GPa-300K"))

    def test_normal_system_name_remains_supported(self) -> None:
        self.assertEqual(
            parse_system_name("Ag-H-50GPa-300K"),
            ("Ag", "50", "300"),
        )


if __name__ == "__main__":
    unittest.main()
