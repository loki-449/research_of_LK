#!/usr/bin/env python3
"""
验证重复部署 scf_ELF 工作流时不会覆盖已有 PBS 脚本。

基本用法:
  python3 -m unittest vasp/tests/test_scf_pbs_preservation.py

参数说明:
  无；测试使用临时目录和 mock，不读写真实计算数据。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

import scf_common
from vasp_common import RelaxStructure


class ScfPbsPreservationTests(unittest.TestCase):
    """覆盖自动部署保留脚本与显式覆盖两种行为。"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.tempdir.name)
        self.pbs = self.base_dir / "scf_ELF" / "ELF.pbs"
        self.pbs.parent.mkdir(parents=True)
        self.custom_pbs = "#PBS -q custom\nCUSTOM_INCAR = TRUE\n"
        self.pbs.write_text(self.custom_pbs, encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def deploy_with_mocked_inputs(self) -> None:
        structure = RelaxStructure(
            elements=["H"],
            counts=[1],
            cell_lines=["1 0 0", "0 1 0", "0 0 1"],
            positions=[("H", 0.0, 0.0, 0.0)],
        )
        with (
            patch.object(scf_common, "parse_relax_in", return_value=structure),
            patch.object(scf_common, "deploy_poscar_to_scf"),
            patch.object(scf_common, "deploy_potcar_to_scf", return_value={}),
        ):
            scf_common.deploy_scf_system("relax.in", self.base_dir)

    def test_automatic_deploy_preserves_existing_elf_pbs(self) -> None:
        self.deploy_with_mocked_inputs()

        self.assertEqual(self.pbs.read_text(encoding="utf-8"), self.custom_pbs)

    def test_first_automatic_deploy_creates_elf_pbs(self) -> None:
        self.pbs.unlink()
        self.deploy_with_mocked_inputs()

        self.assertIn("LELF = TRUE", self.pbs.read_text(encoding="utf-8"))

    def test_explicit_setup_can_still_overwrite_elf_pbs(self) -> None:
        scf_common.setup_scf_scripts(self.base_dir)

        content = self.pbs.read_text(encoding="utf-8")
        self.assertNotEqual(content, self.custom_pbs)
        self.assertIn("LELF = TRUE", content)


if __name__ == "__main__":
    unittest.main()
