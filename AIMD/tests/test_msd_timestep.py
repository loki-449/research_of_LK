#!/usr/bin/env python3
"""
验证 AIMD 帧时间步必须为有限正数。

基本用法:
  python -m unittest discover -s AIMD/tests -v

参数:
  无；测试使用临时目录，不读写真实计算数据。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import resolve_dt


class ResolveTimestepTests(unittest.TestCase):
    """覆盖 INCAR 与命令行两条时间步解析路径。"""

    def test_rejects_nonpositive_potim(self) -> None:
        for value in ("0", "-0.5", "1e309", "-1e309"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                aimd_dir = Path(tmp)
                (aimd_dir / "INCAR").write_text(
                    f"POTIM = {value}\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(ValueError, r"POTIM must be .* > 0"):
                    resolve_dt(aimd_dir)

    def test_rejects_invalid_cli_timestep(self) -> None:
        for value in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(
                    ValueError,
                    r"frame timestep must be finite and > 0",
                ):
                    resolve_dt(tmp, cli_dt=value)

    def test_accepts_positive_timestep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            aimd_dir = Path(tmp)
            (aimd_dir / "INCAR").write_text("POTIM = 0.5\n", encoding="utf-8")

            timestep, source = resolve_dt(aimd_dir)

        self.assertEqual(0.5, timestep)
        self.assertIn("INCAR POTIM=0.5", source)

    def test_accepts_positive_cli_timestep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            timestep, source = resolve_dt(tmp, cli_dt=2.0)

        self.assertEqual(2.0, timestep)
        self.assertEqual("CLI --dt=2.0", source)


if __name__ == "__main__":
    unittest.main()
