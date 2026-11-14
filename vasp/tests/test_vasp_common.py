#!/usr/bin/env python3
"""vasp_common 公共模块回归测试。

基本用法:
  python -m unittest discover -s vasp/tests -v

参数说明:
  无命令行参数；测试仅使用 Python 标准库和临时目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import deploy_opt_system


class QeSpeciesLabelTest(unittest.TestCase):
    """验证 QE 物种标签到 VASP 元素的转换。"""

    def test_numeric_species_suffix_uses_real_element_potcar(self) -> None:
        """Fe1/Fe2 应保留分组，并分别从 Fe 目录选择 POTCAR。"""
        relax_text = """&SYSTEM
 nat = 3, ntyp = 3
/
ATOMIC_SPECIES
Fe1 55.845 Fe.UPF
O 15.999 O.UPF
Fe2 55.845 Fe.UPF
CELL_PARAMETERS angstrom
2.8 0 0
0 2.8 0
0 0 2.8
ATOMIC_POSITIONS crystal
Fe1 0 0 0
O 0.25 0.25 0.25
Fe2 0.5 0.5 0.5
K_POINTS gamma
"""
        fe_potcar_text = """PAW_PBE Fe 06Sep2000
   ZVAL   =  8.000
"""
        o_potcar_text = """PAW_PBE O 08Apr2002
   ZVAL   =  6.000
"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = root / "relax.in"
            relax_in.write_text(relax_text, encoding="utf-8")
            fe_potcar = root / "pbe" / "Fe" / "POTCAR"
            fe_potcar.parent.mkdir(parents=True)
            fe_potcar.write_text(fe_potcar_text, encoding="utf-8")
            o_potcar = root / "pbe" / "O" / "POTCAR"
            o_potcar.parent.mkdir(parents=True)
            o_potcar.write_text(o_potcar_text, encoding="utf-8")

            structure, sources = deploy_opt_system(
                relax_in,
                root / "work" / "Fe" / "0",
                pbe_lib=root / "pbe",
            )

            opt_dir = root / "work" / "Fe" / "0" / "opt"
            poscar_lines = (opt_dir / "POSCAR").read_text(encoding="utf-8").splitlines()
            self.assertEqual(structure.elements, ["Fe1", "O", "Fe2"])
            self.assertEqual(structure.counts, [1, 1, 1])
            self.assertEqual(poscar_lines[5], "Fe1 O Fe2")
            self.assertEqual(poscar_lines[6], "1 1 1")
            self.assertEqual(sources["Fe1"]["dir"], "Fe")
            self.assertEqual(sources["Fe2"]["dir"], "Fe")
            self.assertEqual(
                (opt_dir / "POTCAR").read_text(encoding="utf-8"),
                fe_potcar_text + o_potcar_text + fe_potcar_text,
            )


if __name__ == "__main__":
    unittest.main()
