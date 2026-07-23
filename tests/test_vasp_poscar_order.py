#!/usr/bin/env python3
"""
QE 到 VASP 坐标顺序转换回归测试。

用途:
  验证 QE relax.in 中交错排列的元素坐标会按 POSCAR 元素表重新分组，
  防止 VASP 将坐标错误归属给其他元素。

基本用法:
  python -m unittest tests/test_vasp_poscar_order.py

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VASP_LIB_DIR = REPO_ROOT / "vasp" / "scripts" / "lib"
sys.path.insert(0, str(VASP_LIB_DIR))

from vasp_common import parse_relax_in, write_poscar


class PoscarElementOrderTest(unittest.TestCase):
    """检查交错的 QE 坐标不会改变 VASP 中的元素归属。"""

    def test_interleaved_positions_are_grouped_by_element(self) -> None:
        relax_text = """&control
/
CELL_PARAMETERS angstrom
10.0 0.0 0.0
0.0 10.0 0.0
0.0 0.0 10.0
ATOMIC_POSITIONS crystal
H  0.00 0.00 0.00
Ba 0.50 0.50 0.50
H  0.25 0.25 0.25
K_POINTS gamma
"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            relax_in = tmp_path / "relax.in"
            poscar = tmp_path / "POSCAR"
            relax_in.write_text(relax_text, encoding="utf-8")

            structure = parse_relax_in(relax_in)
            write_poscar(structure, poscar)

            lines = poscar.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[5], "H Ba")
            self.assertEqual(lines[6], "2 1")
            coordinates = [
                tuple(float(value) for value in line.split())
                for line in lines[8:]
            ]
            self.assertEqual(
                coordinates,
                [
                    (0.0, 0.0, 0.0),
                    (0.25, 0.25, 0.25),
                    (0.5, 0.5, 0.5),
                ],
            )


if __name__ == "__main__":
    unittest.main()
