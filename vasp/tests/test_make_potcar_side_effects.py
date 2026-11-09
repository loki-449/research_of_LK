#!/usr/bin/env python3
"""验证单独生成 POTCAR 不会创建或覆盖 opt.pbs。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


OPT_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts" / "opt"
sys.path.insert(0, str(OPT_SCRIPTS_DIR))

import make_potcar


class MakePotcarSideEffectTests(unittest.TestCase):
    """POTCAR 分步入口只负责其声明的输出文件。"""

    def test_arbitrary_output_does_not_create_nested_opt_pbs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scf_ELF" / "POTCAR"

            with patch.object(
                make_potcar,
                "assemble_potcar",
                return_value={"H": {"dir": "H", "zval": 1.0, "date": "01Jan2000"}},
            ):
                make_potcar.make_one(["H"], output, "/unused")

            self.assertFalse((output.parent / "opt" / "opt.pbs").exists())

    def test_system_output_preserves_existing_opt_pbs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            pbs = base / "opt" / "opt.pbs"
            pbs.parent.mkdir(parents=True)
            custom = "#PBS -q custom\nCUSTOM_INCAR = TRUE\n"
            pbs.write_text(custom, encoding="utf-8")

            with patch.object(
                make_potcar,
                "assemble_potcar",
                return_value={"H": {"dir": "H", "zval": 1.0, "date": "01Jan2000"}},
            ):
                make_potcar.make_one(["H"], base / "POTCAR", "/unused")

            self.assertEqual(pbs.read_text(encoding="utf-8"), custom)


if __name__ == "__main__":
    unittest.main()
