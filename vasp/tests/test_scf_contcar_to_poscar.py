#!/usr/bin/env python3
"""
验证 opt/CONTCAR 同步到 scf_ELF/POSCAR 时的 PBS 文件保护。

基本用法:
  python -m unittest discover -s vasp/tests -v

参数:
  无；测试使用临时目录，不读写真实计算数据。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCF_SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "scf_ELF"
sys.path.insert(0, str(SCF_SCRIPT_DIR))

from scf_contcar_to_poscar_ELF import copy_contcar_to_poscar


class CopyContcarToPoscarTests(unittest.TestCase):
    """覆盖 ELF.pbs 已存在及尚未生成两条路径。"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.tempdir.name)
        self.contcar = self.base_dir / "opt" / "CONTCAR"
        self.poscar = self.base_dir / "scf_ELF" / "POSCAR"
        self.pbs = self.poscar.parent / "ELF.pbs"
        self.contcar.parent.mkdir(parents=True)
        self.contcar.write_text("optimized structure\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_write_pbs_preserves_existing_script(self) -> None:
        self.pbs.parent.mkdir(parents=True)
        custom_pbs = "#PBS -q custom\ncustom INCAR settings\n"
        self.pbs.write_text(custom_pbs, encoding="utf-8")

        ok = copy_contcar_to_poscar(
            self.contcar,
            self.poscar,
            write_pbs=True,
        )

        self.assertTrue(ok)
        self.assertEqual("optimized structure\n", self.poscar.read_text(encoding="utf-8"))
        self.assertEqual(custom_pbs, self.pbs.read_text(encoding="utf-8"))

    def test_write_pbs_creates_missing_script(self) -> None:
        ok = copy_contcar_to_poscar(
            self.contcar,
            self.poscar,
            write_pbs=True,
        )

        self.assertTrue(ok)
        self.assertTrue(self.pbs.is_file())
        self.assertIn("LELF = TRUE", self.pbs.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
