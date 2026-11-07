#!/usr/bin/env python3
"""验证 QE 的 Fortran 指数坐标可用于生成 VASP 结构。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import parse_relax_in  # noqa: E402


class QeFortranNumberTests(unittest.TestCase):
    """覆盖 QE 合法的 D/d 指数数值格式。"""

    def test_parses_fortran_exponents_in_atomic_positions(self) -> None:
        relax_text = """\
CELL_PARAMETERS angstrom
3.0 0.0 0.0
0.0 3.0 0.0
0.0 0.0 3.0
ATOMIC_POSITIONS crystal
H 1.25d-1 2.5D-1 0.0d0
K_POINTS gamma
"""
        with tempfile.TemporaryDirectory() as tmp:
            relax_in = Path(tmp) / "relax.in"
            relax_in.write_text(relax_text, encoding="utf-8")
            structure = parse_relax_in(relax_in)

        self.assertEqual(
            structure.positions,
            [("H", 0.125, 0.25, 0.0)],
        )


if __name__ == "__main__":
    unittest.main()
