#!/usr/bin/env python3
"""
验证 QE 后续输入卡片不会被误解析为原子坐标。

基本用法:
  python3 -m unittest vasp/tests/test_relax_card_boundaries.py

参数说明:
  无；测试使用临时 relax.in，不读写真实计算目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import parse_relax_in


BASE_INPUT = """&SYSTEM
 nat = 2
/
CELL_PARAMETERS angstrom
10 0 0
0 10 0
0 0 10
ATOMIC_POSITIONS angstrom
H 0 0 0
O 5 0 0
"""


class RelaxCardBoundaryTests(unittest.TestCase):
    """确保只返回 ATOMIC_POSITIONS 卡片中的真实原子。"""

    def parse_with_suffix(self, suffix: str):
        with tempfile.TemporaryDirectory() as tmp:
            relax_in = Path(tmp) / "relax.in"
            relax_in.write_text(BASE_INPUT + suffix, encoding="utf-8")
            return parse_relax_in(relax_in)

    def assert_two_atom_structure(self, suffix: str) -> None:
        structure = self.parse_with_suffix(suffix)
        self.assertEqual(structure.elements, ["H", "O"])
        self.assertEqual(structure.counts, [1, 1])
        self.assertEqual(len(structure.positions), 2)

    def test_constraints_card_is_not_parsed_as_position(self) -> None:
        self.assert_two_atom_structure(
            "CONSTRAINTS\n"
            "1\n"
            "'fix_atom' 1 1 1 1\n"
        )

    def test_atomic_velocities_are_not_parsed_as_positions(self) -> None:
        self.assert_two_atom_structure(
            "Atomic_Velocities\n"
            "H 0.1 0.2 0.3\n"
            "O 0.0 0.0 0.0\n"
        )

    def test_lowercase_constraints_card_is_not_parsed_as_position(self) -> None:
        self.assert_two_atom_structure(
            "constraints\n"
            "1\n"
            "'fix_atom' 1 1 1 1\n"
        )

    def test_positions_at_end_of_file_remain_supported(self) -> None:
        self.assert_two_atom_structure("")


if __name__ == "__main__":
    unittest.main()
