"""vasp_common 结构解析回归测试。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "vasp" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import parse_relax_in


def relax_input(positions: str, nat: int = 2) -> str:
    return f"""&SYSTEM
  ibrav = 0, nat = {nat}, ntyp = 1,
/
CELL_PARAMETERS angstrom
1 0 0
0 1 0
0 0 1
ATOMIC_POSITIONS crystal
{positions}
K_POINTS gamma
"""


class ParseRelaxInTests(unittest.TestCase):
    def parse_text(self, text: str):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "relax.in"
            source.write_text(text, encoding="utf-8")
            return parse_relax_in(source)

    def test_rejects_fewer_positions_than_declared_nat(self) -> None:
        with self.assertRaisesRegex(ValueError, r"Expected nat=2 .* got 1"):
            self.parse_text(relax_input("H 0 0 0"))

    def test_accepts_position_count_matching_declared_nat(self) -> None:
        structure = self.parse_text(relax_input("H 0 0 0\nH 0.5 0.5 0.5"))
        self.assertEqual(len(structure.positions), 2)
        self.assertEqual(structure.counts, [2])

    def test_reads_nat_only_from_system_namelist(self) -> None:
        text = """&CONTROL
  outdir = './nat=99/'
/
""" + relax_input("H 0 0 0\nH 0.5 0.5 0.5")
        structure = self.parse_text(text)
        self.assertEqual(len(structure.positions), 2)

    def test_reads_nat_when_system_ends_on_same_line(self) -> None:
        text = """&SYSTEM ibrav = 0, nat = 2, label = 'nat=99/' /
CELL_PARAMETERS angstrom
1 0 0
0 1 0
0 0 1
ATOMIC_POSITIONS crystal
H 0 0 0
K_POINTS gamma
"""
        with self.assertRaisesRegex(ValueError, r"Expected nat=2 .* got 1"):
            self.parse_text(text)

    def test_ignores_commented_fake_system_namelist(self) -> None:
        text = "! &SYSTEM nat = 99 /\n" + relax_input(
            "H 0 0 0\nH 0.5 0.5 0.5"
        )
        structure = self.parse_text(text)
        self.assertEqual(len(structure.positions), 2)

    def test_ignores_quoted_fake_system_namelist(self) -> None:
        text = """&CONTROL
  title = '&SYSTEM nat = 99 /'
/
""" + relax_input("H 0 0 0\nH 0.5 0.5 0.5")
        structure = self.parse_text(text)
        self.assertEqual(len(structure.positions), 2)


if __name__ == "__main__":
    unittest.main()
