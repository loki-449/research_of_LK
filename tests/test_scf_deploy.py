#!/usr/bin/env python3
"""
测试 scf_ELF 输入部署对已有优化结构的保护。

基本用法:
  python -m unittest tests.test_scf_deploy

参数说明:
  无命令行参数；测试仅使用标准库和临时目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "vasp" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from scf_common import deploy_scf_system


RELAX_IN = """CELL_PARAMETERS {angstrom}
10.0 0.0 0.0
0.0 10.0 0.0
0.0 0.0 10.0
ATOMIC_POSITIONS {crystal}
H 0.0 0.0 0.0
K_POINTS automatic
1 1 1 0 0 0
"""

OPTIMIZED_POSCAR = """optimized CONTCAR marker
1.0
10.0 0.0 0.0
0.0 10.0 0.0
0.0 0.0 10.0
H
1
Direct
0.25 0.25 0.25
"""


class DeployScfSystemTests(unittest.TestCase):
    """验证默认保留与显式覆盖两种 POSCAR 行为。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.relax_in = self.root / "relax.in"
        self.relax_in.write_text(RELAX_IN, encoding="utf-8")

        self.pbe_lib = self.root / "pbe"
        potcar_dir = self.pbe_lib / "H"
        potcar_dir.mkdir(parents=True)
        (potcar_dir / "POTCAR").write_text(
            "PAW_PBE H 01Jan2001\n   ZVAL = 1.000\n",
            encoding="utf-8",
        )

        self.base_dir = self.root / "work" / "H" / "1"
        self.poscar = self.base_dir / "scf_ELF" / "POSCAR"
        self.poscar.parent.mkdir(parents=True)
        self.poscar.write_text(OPTIMIZED_POSCAR, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_existing_optimized_poscar_is_preserved(self) -> None:
        deploy_scf_system(self.relax_in, self.base_dir, pbe_lib=self.pbe_lib)

        self.assertEqual(self.poscar.read_text(encoding="utf-8"), OPTIMIZED_POSCAR)
        self.assertTrue((self.poscar.parent / "POTCAR").is_file())
        self.assertTrue((self.poscar.parent / "ELF.pbs").is_file())

    def test_explicit_overwrite_replaces_poscar(self) -> None:
        deploy_scf_system(
            self.relax_in,
            self.base_dir,
            pbe_lib=self.pbe_lib,
            overwrite_poscar=True,
        )

        self.assertNotEqual(self.poscar.read_text(encoding="utf-8"), OPTIMIZED_POSCAR)
        self.assertEqual(self.poscar.read_text(encoding="utf-8").splitlines()[0], "POSCAR")

    def test_potcar_failure_does_not_overwrite_poscar(self) -> None:
        with self.assertRaises(FileNotFoundError):
            deploy_scf_system(
                self.relax_in,
                self.base_dir,
                pbe_lib=self.root / "missing-pbe",
                overwrite_poscar=True,
            )

        self.assertEqual(self.poscar.read_text(encoding="utf-8"), OPTIMIZED_POSCAR)


if __name__ == "__main__":
    unittest.main()
