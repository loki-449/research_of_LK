#!/usr/bin/env python3
"""
test_vasp_common.py — VASP 公共结构解析回归测试。

用途:
  验证 QE relax.in 中的非法非有限晶格或原子坐标不会进入 POSCAR 工作流。

基本用法:
  python3 -m unittest discover -s tests -p 'test_*.py'

参数说明:
  无命令行参数；使用 Python 标准库 unittest。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "vasp" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import parse_relax_in


class ParseRelaxInTests(unittest.TestCase):
    """验证 relax.in 数值有效性检查。"""

    def parse_text(self, text: str):
        """将临时 relax.in 文本解析为结构。"""
        with tempfile.TemporaryDirectory() as tmp:
            relax_in = Path(tmp) / "relax.in"
            relax_in.write_text(text, encoding="utf-8")
            return parse_relax_in(relax_in)

    def test_rejects_non_finite_atomic_position(self) -> None:
        text = """\
CELL_PARAMETERS angstrom
1 0 0
0 1 0
0 0 1
ATOMIC_POSITIONS crystal
H nan 0.25 0.5
K_POINTS gamma
"""
        with self.assertRaisesRegex(ValueError, "Non-finite atomic position"):
            self.parse_text(text)

    def test_rejects_non_finite_cell_vector(self) -> None:
        text = """\
CELL_PARAMETERS angstrom
1 0 0
0 1e309 0
0 0 1
ATOMIC_POSITIONS crystal
H 0 0.25 0.5
K_POINTS gamma
"""
        with self.assertRaisesRegex(ValueError, "Non-finite cell vector"):
            self.parse_text(text)

    def test_accepts_finite_structure(self) -> None:
        text = """\
CELL_PARAMETERS angstrom
1 0 0
0 1 0
0 0 1
ATOMIC_POSITIONS crystal
H 0 0.25 0.5
K_POINTS gamma
"""
        structure = self.parse_text(text)

        self.assertEqual(structure.elements, ["H"])
        self.assertEqual(structure.positions, [("H", 0.0, 0.25, 0.5)])

    def test_accepts_fortran_exponents(self) -> None:
        text = """\
CELL_PARAMETERS angstrom
1.0D+00 0 0
0 1.0d+00 0
0 0 1.0D+00
ATOMIC_POSITIONS crystal
H 0.0D+00 2.5d-01 5.0D-01
K_POINTS gamma
"""
        structure = self.parse_text(text)

        self.assertEqual(structure.positions, [("H", 0.0, 0.25, 0.5)])


if __name__ == "__main__":
    unittest.main()
