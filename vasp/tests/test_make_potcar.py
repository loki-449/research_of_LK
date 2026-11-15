#!/usr/bin/env python3
"""
test_make_potcar.py — make_potcar 元素顺序一致性回归测试。

用途:
  验证标准 opt/POTCAR 不会被与同目录 POSCAR 元素顺序不一致的赝势覆盖。

基本用法:
  python3 -m unittest vasp/tests/test_make_potcar.py -v

参数说明:
  无；测试仅使用临时 POSCAR 与赝势库，不修改真实计算数据。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "vasp" / "scripts" / "opt" / "make_potcar.py"


class MakePotcarTests(unittest.TestCase):
    """标准 opt/POTCAR 必须与同目录 POSCAR 的元素顺序一致。"""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.opt_dir = self.root / "calc" / "AgH" / "50" / "opt"
        self.opt_dir.mkdir(parents=True)
        (self.opt_dir / "POSCAR").write_text(
            "AgH\n"
            "1.0\n"
            "1 0 0\n"
            "0 1 0\n"
            "0 0 1\n"
            "Ag H\n"
            "1 1\n"
            "Direct\n"
            "0 0 0\n"
            "0.5 0.5 0.5\n",
            encoding="utf-8",
        )

        self.pbe_lib = self.root / "pbe"
        self._write_potential("Ag", 11.0)
        self._write_potential("H", 1.0)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _write_potential(self, element: str, zval: float) -> None:
        directory = self.pbe_lib / element
        directory.mkdir(parents=True)
        (directory / "POTCAR").write_text(
            f"PAW_PBE {element} 01Jan2000\n"
            f"ZVAL = {zval}\n"
            f"{element}-payload\n",
            encoding="utf-8",
        )

    def _run(self, *elements: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                *elements,
                "--pbe-lib",
                str(self.pbe_lib),
                "-o",
                str(self.opt_dir / "POTCAR"),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_mismatch_is_rejected_without_overwriting_existing_potcar(self) -> None:
        potcar = self.opt_dir / "POTCAR"
        potcar.write_bytes(b"existing-valid-potcar\n")

        result = self._run("H", "Ag")

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("does not match sibling POSCAR", result.stdout)
        self.assertEqual(potcar.read_bytes(), b"existing-valid-potcar\n")
        self.assertFalse((self.opt_dir / "Ag.POTCAR").exists())
        self.assertFalse((self.opt_dir / "H.POTCAR").exists())

    def test_default_relative_output_in_opt_cannot_bypass_validation(self) -> None:
        potcar = self.opt_dir / "POTCAR"
        potcar.write_bytes(b"existing-valid-potcar\n")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "H",
                "Ag",
                "--pbe-lib",
                str(self.pbe_lib),
            ],
            cwd=self.opt_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("does not match sibling POSCAR", result.stdout)
        self.assertEqual(potcar.read_bytes(), b"existing-valid-potcar\n")

    def test_symlinked_standard_output_cannot_bypass_validation(self) -> None:
        external_target = self.root / "external-potcar"
        external_target.write_bytes(b"external-valid-potcar\n")
        (self.opt_dir / "POTCAR").symlink_to(external_target)

        result = self._run("H", "Ag")

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("does not match sibling POSCAR", result.stdout)
        self.assertEqual(external_target.read_bytes(), b"external-valid-potcar\n")

    def test_matching_order_writes_potcar(self) -> None:
        result = self._run("Ag", "H")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        content = (self.opt_dir / "POTCAR").read_text(encoding="utf-8")
        self.assertLess(content.index("Ag-payload"), content.index("H-payload"))


if __name__ == "__main__":
    unittest.main()
