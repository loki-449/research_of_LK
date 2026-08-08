"""scf_contcar_to_poscar_ELF.py 的回归测试。"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR / "lib"))
MODULE_PATH = SCRIPTS_DIR / "scf_ELF" / "scf_contcar_to_poscar_ELF.py"
SPEC = importlib.util.spec_from_file_location("scf_contcar_to_poscar_ELF", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SCF_COPY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCF_COPY)

VALID_CONTCAR = """optimized structure
1.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H He
1 1
Selective dynamics
Direct
0.0 0.0 0.0 T T T
0.5 0.5 0.5 F F F
"""


class CopyContcarTests(unittest.TestCase):
    def test_empty_contcar_does_not_replace_existing_poscar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contcar = root / "CONTCAR"
            poscar = root / "POSCAR"
            contcar.write_bytes(b"")
            poscar.write_text("existing valid input\n", encoding="utf-8")

            self.assertFalse(SCF_COPY.copy_contcar_to_poscar(contcar, poscar))
            self.assertEqual(
                poscar.read_text(encoding="utf-8"), "existing valid input\n"
            )

    def test_truncated_contcar_does_not_replace_existing_poscar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contcar = root / "CONTCAR"
            poscar = root / "POSCAR"
            contcar.write_text(
                VALID_CONTCAR.rsplit("0.5 0.5 0.5 F F F\n", 1)[0],
                encoding="utf-8",
            )
            poscar.write_text("existing valid input\n", encoding="utf-8")

            self.assertFalse(SCF_COPY.copy_contcar_to_poscar(contcar, poscar))
            self.assertEqual(
                poscar.read_text(encoding="utf-8"), "existing valid input\n"
            )

    def test_complete_contcar_replaces_poscar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contcar = root / "CONTCAR"
            poscar = root / "scf_ELF" / "POSCAR"
            contcar.write_text(VALID_CONTCAR, encoding="utf-8")

            self.assertTrue(SCF_COPY.copy_contcar_to_poscar(contcar, poscar))
            self.assertEqual(poscar.read_text(encoding="utf-8"), VALID_CONTCAR)

    def test_batch_reports_failure_for_invalid_contcar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            contcar = work_root / "H" / "100" / "opt" / "CONTCAR"
            poscar = work_root / "H" / "100" / "scf_ELF" / "POSCAR"
            contcar.parent.mkdir(parents=True)
            poscar.parent.mkdir(parents=True)
            contcar.write_bytes(b"")
            poscar.write_text("existing valid input\n", encoding="utf-8")

            self.assertEqual(SCF_COPY.batch_scan(work_root), 1)
            self.assertEqual(
                poscar.read_text(encoding="utf-8"), "existing valid input\n"
            )


if __name__ == "__main__":
    unittest.main()
