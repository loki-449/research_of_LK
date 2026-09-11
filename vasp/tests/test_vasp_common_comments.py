#!/usr/bin/env python3
"""
test_vasp_common_comments.py — QE 结构卡片注释解析回归测试

用途:
  验证 relax.in 中合法的整行 ``!``/``#`` 注释不会被误作晶格或原子坐标，
  防止生成无法由 VASP 读取的 POSCAR。

基本用法:
  python3 -m unittest vasp/tests/test_vasp_common_comments.py -v

参数说明:
  无。测试仅使用临时文件，不依赖 QE、VASP 或第三方库。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import parse_relax_in, write_poscar  # noqa: E402


class QeCardCommentTests(unittest.TestCase):
    """验证 QE card 中的整行注释在结构转换前被忽略。"""

    def test_comment_lines_do_not_enter_poscar_structure(self) -> None:
        """注释中的 card 名、坐标和晶格说明均不应污染 POSCAR。"""
        relax_text = """&CONTROL
 calculation = 'relax'
/
&SYSTEM
 ibrav = 0, nat = 2, ntyp = 2
/
ATOMIC_SPECIES
H  1.0  H.UPF
He 4.0  He.UPF
! ATOMIC_POSITIONS from an older structure
ATOMIC_POSITIONS crystal
# first atom follows
H  0.0  0.0  0.0
! He 0.1 0.1 0.1 is intentionally disabled
He 0.5  0.5  0.5
K_POINTS gamma
CELL_PARAMETERS angstrom
! lattice vectors in angstrom
# the active cell follows
3.0 0.0 0.0
0.0 3.0 0.0
0.0 0.0 3.0
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = root / "relax.in"
            relax_in.write_text(relax_text, encoding="utf-8")

            structure = parse_relax_in(relax_in)
            output = write_poscar(structure, root / "POSCAR")
            lines = output.read_text(encoding="utf-8").splitlines()

        self.assertEqual(structure.elements, ["H", "He"])
        self.assertEqual(structure.counts, [1, 1])
        self.assertEqual(
            structure.cell_lines,
            ["3.0 0.0 0.0", "0.0 3.0 0.0", "0.0 0.0 3.0"],
        )
        self.assertEqual(lines[2:5], structure.cell_lines)
        self.assertEqual(lines[5], "H He")
        self.assertEqual(lines[6], "1 1")
        self.assertEqual(len(lines), 10)


if __name__ == "__main__":
    unittest.main()
