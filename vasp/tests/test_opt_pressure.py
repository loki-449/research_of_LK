#!/usr/bin/env python3
"""
test_opt_pressure.py — VASP 变胞优化目标压强回归测试。

用途:
  验证体系目录中的 GPa 压强会转换为 PSTRESS 所需的 kB，并写入 opt.pbs。

基本用法:
  python -m unittest discover -s vasp/tests -v

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vasp_common import setup_opt_scripts, write_opt_pbs  # noqa: E402


class OptPressureTests(unittest.TestCase):
    """验证 opt PBS 中的目标外压。"""

    def test_setup_converts_integer_gpa_to_kbar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp) / "Ag" / "50"

            opt_dir = setup_opt_scripts(base_dir)

            script = (opt_dir / "opt.pbs").read_text(encoding="utf-8")
            self.assertIn("PSTRESS = 500\n", script)

    def test_setup_converts_decimal_gpa_to_kbar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp) / "FeO" / "12.5"

            opt_dir = setup_opt_scripts(base_dir)

            script = (opt_dir / "opt.pbs").read_text(encoding="utf-8")
            self.assertIn("PSTRESS = 125\n", script)

    def test_legacy_writer_infers_pressure_from_opt_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            opt_dir = Path(tmp) / "Ag" / "50" / "opt"

            script_path = write_opt_pbs(opt_dir)

            script = script_path.read_text(encoding="utf-8")
            self.assertIn("PSTRESS = 500\n", script)

    def test_non_numeric_custom_base_keeps_zero_pressure_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp) / "custom"

            opt_dir = setup_opt_scripts(base_dir)

            script = (opt_dir / "opt.pbs").read_text(encoding="utf-8")
            self.assertNotIn("PSTRESS", script)


if __name__ == "__main__":
    unittest.main()
