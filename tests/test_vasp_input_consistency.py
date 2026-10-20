#!/usr/bin/env python3
"""
测试 VASP POSCAR/POTCAR 元素顺序一致性校验。

基本用法:
  python -m unittest tests.test_vasp_input_consistency

参数:
  无。测试使用临时目录，不读写正式计算数据。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "vasp" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import vasp_inputs_complete


class VaspInputsCompleteTests(unittest.TestCase):
    """覆盖匹配、错配及损坏 POTCAR。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_poscar(self, elements: str) -> None:
        self.work_dir.joinpath("POSCAR").write_text(
            "\n".join(
                [
                    "test",
                    "1.0",
                    "1 0 0",
                    "0 1 0",
                    "0 0 1",
                    elements,
                    "1 1",
                    "Direct",
                    "0 0 0",
                    "0.5 0.5 0.5",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def write_potcar(self, *elements: str) -> None:
        sections = [
            f"PAW_PBE {element} 01Jan2000\n"
            f"   TITEL  = PAW_PBE {element}_pv 01Jan2000\n"
            "End of Dataset\n"
            for element in elements
        ]
        self.work_dir.joinpath("POTCAR").write_text(
            "".join(sections),
            encoding="utf-8",
        )

    def test_matching_element_order_is_complete(self) -> None:
        self.write_poscar("Ag Li")
        self.write_potcar("Ag", "Li")

        self.assertTrue(vasp_inputs_complete(self.work_dir))

    def test_stale_potcar_is_not_complete(self) -> None:
        self.write_poscar("Ag Li")
        self.write_potcar("Ag", "H")

        self.assertFalse(vasp_inputs_complete(self.work_dir))

    def test_unparseable_potcar_is_not_complete(self) -> None:
        self.write_poscar("Ag Li")
        self.work_dir.joinpath("POTCAR").write_text(
            "truncated pseudopotential\n",
            encoding="utf-8",
        )

        self.assertFalse(vasp_inputs_complete(self.work_dir))

    def test_potcar_truncated_after_title_is_not_complete(self) -> None:
        self.write_poscar("Ag Li")
        self.work_dir.joinpath("POTCAR").write_text(
            "   TITEL  = PAW_PBE Ag_pv 01Jan2000\n"
            "End of Dataset\n"
            "   TITEL  = PAW_PBE Li_sv 01Jan2000\n",
            encoding="utf-8",
        )

        self.assertFalse(vasp_inputs_complete(self.work_dir))

    def test_missing_input_is_not_complete(self) -> None:
        self.assertFalse(vasp_inputs_complete(self.work_dir))


if __name__ == "__main__":
    unittest.main()
