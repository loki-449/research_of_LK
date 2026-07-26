#!/usr/bin/env python3
"""
test_vasp_common.py — VASP 公共结构转换逻辑回归测试

用途:
  验证 QE relax.in 的晶格和原子坐标单位能被正确写入 VASP POSCAR，
  并确保无法安全转换的 alat 输入不会静默生成错误结构。

基本用法:
  python -m unittest tests.test_vasp_common

参数说明:
  无命令行参数；仅使用 Python 标准库 unittest。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vasp" / "scripts" / "lib"))

from vasp_common import BOHR_TO_ANGSTROM, parse_relax_in, write_poscar


class QeUnitConversionTests(unittest.TestCase):
    """验证 QE card 单位到 POSCAR 语义的转换。"""

    def _write_relax_in(self, directory: Path, text: str) -> Path:
        relax_in = directory / "relax.in"
        relax_in.write_text(text, encoding="utf-8")
        return relax_in

    def test_angstrom_positions_are_written_as_cartesian(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = self._write_relax_in(
                root,
                """CELL_PARAMETERS (angstrom)
3.0 0.0 0.0
0.0 3.0 0.0
0.0 0.0 3.0
ATOMIC_POSITIONS (angstrom)
H 1.5 0.0 0.0
K_POINTS gamma
""",
            )

            structure = parse_relax_in(relax_in)
            output = write_poscar(structure, root / "POSCAR")
            lines = output.read_text(encoding="utf-8").splitlines()

            self.assertEqual(
                [float(value) for value in lines[2].split()],
                [3.0, 0.0, 0.0],
            )
            self.assertEqual(lines[7], "Cartesian")
            self.assertEqual(
                [float(value) for value in lines[8].split()],
                [1.5, 0.0, 0.0],
            )

    def test_crystal_positions_remain_direct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = self._write_relax_in(
                root,
                """CELL_PARAMETERS angstrom
3.0 0.0 0.0
0.0 3.0 0.0
0.0 0.0 3.0
ATOMIC_POSITIONS crystal
H 0.5 0.0 0.0
K_POINTS gamma
""",
            )

            structure = parse_relax_in(relax_in)
            output = write_poscar(structure, root / "POSCAR")
            lines = output.read_text(encoding="utf-8").splitlines()

            self.assertEqual(lines[7], "Direct")
            self.assertEqual(
                [float(value) for value in lines[8].split()],
                [0.5, 0.0, 0.0],
            )

    def test_bohr_cell_and_positions_are_converted_to_angstrom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = self._write_relax_in(
                root,
                """CELL_PARAMETERS {bohr}
2.0 0.0 0.0
0.0 2.0 0.0
0.0 0.0 2.0
ATOMIC_POSITIONS {bohr}
H 1.0 0.0 0.0
K_POINTS gamma
""",
            )

            structure = parse_relax_in(relax_in)
            output = write_poscar(structure, root / "POSCAR")
            lines = output.read_text(encoding="utf-8").splitlines()

            self.assertAlmostEqual(float(lines[2].split()[0]), 2 * BOHR_TO_ANGSTROM)
            self.assertEqual(lines[7], "Cartesian")
            self.assertAlmostEqual(float(lines[8].split()[0]), BOHR_TO_ANGSTROM)

    def test_alat_input_is_rejected_instead_of_written_as_direct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = self._write_relax_in(
                root,
                """CELL_PARAMETERS angstrom
3.0 0.0 0.0
0.0 3.0 0.0
0.0 0.0 3.0
ATOMIC_POSITIONS alat
H 0.5 0.0 0.0
K_POINTS gamma
""",
            )

            with self.assertRaisesRegex(ValueError, "ATOMIC_POSITIONS alat"):
                parse_relax_in(relax_in)

    def test_implicit_alat_cell_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = self._write_relax_in(
                root,
                """CELL_PARAMETERS
3.0 0.0 0.0
0.0 3.0 0.0
0.0 0.0 3.0
ATOMIC_POSITIONS crystal
H 0.5 0.0 0.0
K_POINTS gamma
""",
            )

            with self.assertRaisesRegex(ValueError, "CELL_PARAMETERS alat"):
                parse_relax_in(relax_in)

    def test_crystal_sg_positions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = self._write_relax_in(
                root,
                """CELL_PARAMETERS angstrom
3.0 0.0 0.0
0.0 3.0 0.0
0.0 0.0 3.0
ATOMIC_POSITIONS crystal_sg
H 0.0 0.0 0.0
K_POINTS gamma
""",
            )

            with self.assertRaisesRegex(ValueError, "crystal_sg"):
                parse_relax_in(relax_in)


if __name__ == "__main__":
    unittest.main()
