#!/usr/bin/env python3
"""
QE 原子约束到 VASP Selective dynamics 的回归测试。

用途:
  验证 relax.in 的 if_pos 标志会被保留到 POSCAR，防止固定原子在
  VASP 结构优化中被静默释放。

基本用法:
  python -m unittest tests.test_vasp_selective_dynamics

参数说明:
  无命令行参数；仅使用 Python 标准库 unittest。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "vasp" / "scripts" / "lib"))

from vasp_common import parse_relax_in, write_poscar


class SelectiveDynamicsTests(unittest.TestCase):
    """检查 QE if_pos 与 VASP 自由度标志的转换。"""

    def _write_poscar(self, relax_text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = root / "relax.in"
            poscar = root / "POSCAR"
            relax_in.write_text(relax_text, encoding="utf-8")
            write_poscar(parse_relax_in(relax_in), poscar)
            return poscar.read_text(encoding="utf-8").splitlines()

    def test_if_pos_flags_are_written_as_selective_dynamics(self) -> None:
        lines = self._write_poscar(
            """CELL_PARAMETERS angstrom
5.0 0.0 0.0
0.0 5.0 0.0
0.0 0.0 5.0
ATOMIC_POSITIONS crystal
O 0.0 0.0 0.0 0 1 0 ! only y is free
H 0.1 0.0 0.0
K_POINTS gamma
"""
        )

        self.assertEqual(lines[7], "Selective dynamics")
        self.assertEqual(lines[8], "Direct")
        self.assertEqual(lines[9].split()[-3:], ["F", "T", "F"])
        self.assertEqual(lines[10].split()[-3:], ["T", "T", "T"])

    def test_unconstrained_input_keeps_standard_poscar_layout(self) -> None:
        lines = self._write_poscar(
            """CELL_PARAMETERS angstrom
5.0 0.0 0.0
0.0 5.0 0.0
0.0 0.0 5.0
ATOMIC_POSITIONS crystal
H 0.0 0.0 0.0
K_POINTS gamma
"""
        )

        self.assertEqual(lines[7], "Direct")
        self.assertEqual(len(lines[8].split()), 3)

    def test_partial_if_pos_flags_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            relax_in = Path(tmp) / "relax.in"
            relax_in.write_text(
                """CELL_PARAMETERS angstrom
5.0 0.0 0.0
0.0 5.0 0.0
0.0 0.0 5.0
ATOMIC_POSITIONS crystal
H 0.0 0.0 0.0 0 1
K_POINTS gamma
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Incomplete QE if_pos"):
                parse_relax_in(relax_in)


if __name__ == "__main__":
    unittest.main()
