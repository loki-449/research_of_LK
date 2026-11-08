from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import RelaxStructure, deploy_poscar_to_opt


class DeployPoscarToOptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.structure = RelaxStructure(
            elements=["H"],
            counts=[1],
            cell_lines=["1 0 0", "0 1 0", "0 0 1"],
            positions=[("H", 0.0, 0.0, 0.0)],
        )

    def test_writes_poscar_before_vasp_creates_contcar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp) / "H" / "50"

            result = deploy_poscar_to_opt(self.structure, base_dir)

            self.assertEqual(result, base_dir / "opt" / "POSCAR")
            self.assertIn("H\n1\nDirect\n", result.read_text(encoding="utf-8"))

    def test_preserves_poscar_after_vasp_created_contcar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp) / "H" / "50"
            opt_dir = base_dir / "opt"
            opt_dir.mkdir(parents=True)
            poscar = opt_dir / "POSCAR"
            poscar.write_text("existing optimized input\n", encoding="utf-8")
            (opt_dir / "CONTCAR").write_text("relaxed structure\n", encoding="utf-8")

            with self.assertRaisesRegex(
                FileExistsError, "Refusing to replace opt/POSCAR"
            ):
                deploy_poscar_to_opt(self.structure, base_dir)

            self.assertEqual(
                poscar.read_text(encoding="utf-8"), "existing optimized input\n"
            )


if __name__ == "__main__":
    unittest.main()
