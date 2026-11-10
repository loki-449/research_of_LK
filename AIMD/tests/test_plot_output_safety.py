#!/usr/bin/env python3
"""验证绘图输出不会覆盖 XDATCAR 或 MSD 数据输入。

基本用法:
  python3 -m unittest AIMD/tests/test_plot_output_safety.py

参数说明:
  无命令行参数；测试仅使用临时文件。
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "MSD_RMSD"
sys.path.insert(0, str(SCRIPT_DIR))

import plot_msd_flex  # noqa: E402
import xdatcar_msd_flex  # noqa: E402


class PlotOutputSafetyTests(unittest.TestCase):
    """覆盖符号链接、硬链接和正常无扩展名输出。"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.system_dir = self.root / "sample"
        self.aimd_dir = self.system_dir / "AIMD"
        self.aimd_dir.mkdir(parents=True)

        self.xdatcar = self.aimd_dir / "XDATCAR"
        self.xdatcar_bytes = (
            b"test\n1.0\n1 0 0\n0 1 0\n0 0 1\nH\n1\n"
            b"Direct configuration= 1\n0 0 0\n"
            b"Direct configuration= 2\n0.1 0 0\n"
        )
        self.xdatcar.write_bytes(self.xdatcar_bytes)

        self.dat = self.system_dir / "msd_data.dat"
        self.dat_bytes = (
            b"# Time(ps) H_MSD(A2) H_RMSD(A)\n"
            b"0.0 0.0 0.0\n"
            b"0.1 0.01 0.1\n"
        )
        self.dat.write_bytes(self.dat_bytes)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_xdatcar_plot_rejects_symbolic_link_output(self) -> None:
        output = self.root / "trajectory.png"
        output.symlink_to(self.xdatcar)

        with contextlib.redirect_stdout(io.StringIO()):
            result = xdatcar_msd_flex.main(
                [
                    str(self.xdatcar),
                    "--dt",
                    "1.0",
                    "--output",
                    str(output),
                    "--no-publish",
                ]
            )

        self.assertEqual(result, 1)
        self.assertEqual(self.xdatcar.read_bytes(), self.xdatcar_bytes)

    def test_dat_plot_rejects_hard_link_output(self) -> None:
        output = self.root / "data.png"
        os.link(self.dat, output)

        with contextlib.redirect_stdout(io.StringIO()):
            result = plot_msd_flex.main(
                [str(self.dat), "--output", str(output), "--no-publish"]
            )

        self.assertEqual(result, 1)
        self.assertEqual(self.dat.read_bytes(), self.dat_bytes)

    def test_extensionless_output_keeps_input_and_writes_png(self) -> None:
        output = self.root / "plot"

        with contextlib.redirect_stdout(io.StringIO()):
            result = xdatcar_msd_flex.main(
                [
                    str(self.xdatcar),
                    "--dt",
                    "1.0",
                    "--output",
                    str(output),
                    "--no-publish",
                ]
            )

        self.assertEqual(result, 0)
        self.assertEqual(self.xdatcar.read_bytes(), self.xdatcar_bytes)
        self.assertTrue((self.root / "plot.png").is_file())


if __name__ == "__main__":
    unittest.main()
