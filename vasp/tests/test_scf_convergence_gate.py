#!/usr/bin/env python3
"""测试 CONTCAR 晋级到 scf_ELF/POSCAR 前的收敛保护。"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "scf_ELF"
    / "scf_contcar_to_poscar_ELF.py"
)
SPEC = importlib.util.spec_from_file_location("scf_contcar_to_poscar_elf", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CopyContcarTests(unittest.TestCase):
    """覆盖收敛、未收敛和显式覆盖三条路径。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.opt_dir = self.root / "Ag" / "50" / "opt"
        self.opt_dir.mkdir(parents=True)
        self.contcar = self.opt_dir / "CONTCAR"
        self.contcar.write_text("new relaxed structure\n", encoding="utf-8")
        self.poscar = self.root / "Ag" / "50" / "scf_ELF" / "POSCAR"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_unconverged_outcar_does_not_overwrite_existing_poscar(self) -> None:
        self.poscar.parent.mkdir(parents=True)
        self.poscar.write_text("previous valid structure\n", encoding="utf-8")
        (self.opt_dir / "OUTCAR").write_text(
            "running ionic step 12\n", encoding="utf-8"
        )

        copied = MODULE.copy_contcar_to_poscar(self.contcar, self.poscar)

        self.assertFalse(copied)
        self.assertEqual(
            self.poscar.read_text(encoding="utf-8"), "previous valid structure\n"
        )

    def test_converged_outcar_allows_copy(self) -> None:
        (self.opt_dir / "OUTCAR").write_text(
            f"{MODULE.IONIC_CONVERGENCE_MARKER}\n", encoding="utf-8"
        )

        copied = MODULE.copy_contcar_to_poscar(self.contcar, self.poscar)

        self.assertTrue(copied)
        self.assertEqual(
            self.poscar.read_text(encoding="utf-8"), "new relaxed structure\n"
        )

    def test_explicit_override_allows_intermediate_structure(self) -> None:
        copied = MODULE.copy_contcar_to_poscar(
            self.contcar,
            self.poscar,
            allow_unconverged=True,
        )

        self.assertTrue(copied)
        self.assertEqual(
            self.poscar.read_text(encoding="utf-8"), "new relaxed structure\n"
        )


if __name__ == "__main__":
    unittest.main()
