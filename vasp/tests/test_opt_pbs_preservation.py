#!/usr/bin/env python3
"""
验证重复部署 opt 工作流时不会覆盖已有 PBS 脚本。

基本用法:
  python3 -m unittest vasp/tests/test_opt_pbs_preservation.py

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

import vasp_common
from vasp_common import RelaxStructure


class OptPbsPreservationTests(unittest.TestCase):
    """覆盖自动部署保留脚本与显式覆盖两种行为。"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.tempdir.name)
        self.pbs = self.base_dir / "opt" / "opt.pbs"
        self.pbs.parent.mkdir(parents=True)
        self.custom_pbs = "#PBS -q custom\nCUSTOM_INCAR = TRUE\n"
        self.pbs.write_text(self.custom_pbs, encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_automatic_deploy_preserves_existing_opt_pbs(self) -> None:
        structure = RelaxStructure(
            elements=["H"],
            counts=[1],
            cell_lines=["1 0 0", "0 1 0", "0 0 1"],
            positions=[("H", 0.0, 0.0, 0.0)],
        )
        with (
            patch.object(vasp_common, "parse_relax_in", return_value=structure),
            patch.object(vasp_common, "deploy_poscar_to_opt"),
            patch.object(vasp_common, "deploy_potcar_to_opt", return_value={}),
        ):
            vasp_common.deploy_opt_system("relax.in", self.base_dir)

        self.assertEqual(self.pbs.read_text(encoding="utf-8"), self.custom_pbs)

    def test_explicit_setup_can_still_overwrite_opt_pbs(self) -> None:
        vasp_common.setup_opt_scripts(self.base_dir, overwrite=True)

        content = self.pbs.read_text(encoding="utf-8")
        self.assertNotEqual(content, self.custom_pbs)
        self.assertIn("SYSTEM = Relaxation", content)


if __name__ == "__main__":
    unittest.main()
