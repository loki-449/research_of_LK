#!/usr/bin/env python3
"""
test_legacy_entrypoints.py — AIMD 历史入口兼容转发回归测试。

用途:
  验证 AIMD/MSD&RMSD 下的旧 flex 命令执行当前脚本包，而不是继续运行
  默认时间步为 1 fs 的旧算法副本。

基本用法:
  python3 -m unittest AIMD/tests/test_legacy_entrypoints.py -v

参数说明:
  无；测试使用临时 XDATCAR/INCAR，不修改真实计算数据。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_DIR = REPO_ROOT / "AIMD" / "MSD&RMSD"


class LegacyEntrypointTests(unittest.TestCase):
    """历史命令必须转发到规范实现并继承其行为。"""

    def run_legacy(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(LEGACY_DIR / script), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_extract_uses_potim_from_incar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system_dir = Path(tmp) / "Sample"
            aimd_dir = system_dir / "AIMD"
            aimd_dir.mkdir(parents=True)
            (aimd_dir / "INCAR").write_text("POTIM = 2.0\n", encoding="utf-8")
            xdatcar = aimd_dir / "XDATCAR"
            xdatcar.write_text(
                "Sample\n"
                "1.0\n"
                "1 0 0\n"
                "0 1 0\n"
                "0 0 1\n"
                "H\n"
                "1\n"
                "Direct configuration= 1\n"
                "0.0 0.0 0.0\n"
                "Direct configuration= 2\n"
                "0.1 0.0 0.0\n",
                encoding="utf-8",
            )
            output = Path(tmp) / "msd.dat"

            result = self.run_legacy(
                "extract_msd_flex.py",
                str(xdatcar),
                "--stride",
                "1",
                "--no-publish",
                "-o",
                str(output),
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("正在转发", result.stderr)
            rows = [
                line.split()
                for line in output.read_text(encoding="utf-8").splitlines()
                if line and not line.startswith("#")
            ]
            self.assertEqual(len(rows), 2)
            self.assertAlmostEqual(float(rows[1][0]), 0.002)

    def test_other_flex_commands_expose_current_cli(self) -> None:
        expectations = {
            "xdatcar_msd_flex.py": "--write-dat",
            "plot_msd_flex.py": "--system-dir",
        }
        for script, option in expectations.items():
            with self.subTest(script=script):
                result = self.run_legacy(script, "--help")
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertIn("正在转发", result.stderr)
                self.assertIn(option, result.stdout)


if __name__ == "__main__":
    unittest.main()
