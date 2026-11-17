#!/usr/bin/env python3
"""
验证 CONTCAR → SCF POSCAR 入口严格区分批量、单体系和显式文件模式。

基本用法:
  python -m unittest tests/test_scf_contcar_cli_modes.py

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "vasp" / "scripts" / "scf_ELF"
sys.path.insert(0, str(SCRIPT_DIR))

import scf_contcar_to_poscar_ELF as contcar_cli


class ScfContcarCliModeTest(unittest.TestCase):
    """冲突 CLI 模式必须在任何文件写入前失败。"""

    def test_conflicting_modes_do_not_overwrite_poscars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp) / "production"
            target = work_root / "Ag" / "50"
            other = work_root / "Ba" / "100"

            for base, old_value in ((target, "target-old"), (other, "other-old")):
                (base / "opt").mkdir(parents=True)
                (base / "scf_ELF").mkdir()
                (base / "opt" / "CONTCAR").write_text(
                    f"{base.name}-new\n", encoding="utf-8"
                )
                (base / "scf_ELF" / "POSCAR").write_text(
                    old_value, encoding="utf-8"
                )

            explicit_output = Path(tmp) / "explicit" / "POSCAR"
            conflicting_argv = (
                [
                    "--scan",
                    "--system-dir",
                    str(target),
                    "--work-root",
                    str(work_root),
                ],
                [
                    "--scan",
                    "--contcar",
                    str(target / "opt" / "CONTCAR"),
                    "--output",
                    str(explicit_output),
                    "--work-root",
                    str(work_root),
                ],
                [
                    "--system-dir",
                    str(target),
                    "--contcar",
                    str(target / "opt" / "CONTCAR"),
                    "--output",
                    str(explicit_output),
                ],
            )

            for argv in conflicting_argv:
                with self.subTest(argv=argv):
                    with self.assertRaisesRegex(SystemExit, "2"):
                        contcar_cli.main(argv)
                    self.assertEqual(
                        (target / "scf_ELF" / "POSCAR").read_text(encoding="utf-8"),
                        "target-old",
                    )
                    self.assertEqual(
                        (other / "scf_ELF" / "POSCAR").read_text(encoding="utf-8"),
                        "other-old",
                    )
                    self.assertFalse(explicit_output.exists())

    def test_explicit_file_arguments_must_be_paired(self) -> None:
        with self.assertRaisesRegex(SystemExit, "2"):
            contcar_cli.main(["--contcar", "/tmp/CONTCAR"])
        with self.assertRaisesRegex(SystemExit, "2"):
            contcar_cli.main(["--scan", "--output", "/tmp/POSCAR"])

    def test_each_single_mode_and_deprecated_alias_remains_accepted(self) -> None:
        parser = contcar_cli.build_parser()
        accepted = (
            ["--scan"],
            ["--system-dir", "/calc/Ag/50"],
            ["--opt-dir", "/calc/Ag/50"],
            ["--contcar", "/calc/CONTCAR", "--output", "/calc/POSCAR"],
        )
        for argv in accepted:
            with self.subTest(argv=argv):
                parser.parse_args(argv)


if __name__ == "__main__":
    unittest.main()
