#!/usr/bin/env python3
"""测试 AIMD 批处理在跳过已有 DAT 时仍能补全绘图产物。

基本用法:
  python3 -m unittest AIMD/tests/test_run_msd_batch.py

参数说明:
  无命令行参数；测试使用临时工作目录，不读写真实计算数据。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "MSD_RMSD"
sys.path.insert(0, str(SCRIPT_DIR))

import run_msd_batch  # noqa: E402


class SkipExistingPlotTests(unittest.TestCase):
    """验证 --skip-existing 与 --with-plot 的组合行为。"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.work_root = Path(self.tempdir.name)
        aimd_dir = self.work_root / "sample" / "AIMD"
        aimd_dir.mkdir(parents=True)
        (aimd_dir / "XDATCAR").write_text("", encoding="utf-8")

        dat_dir = self.work_root / "MSD_data_for_origin"
        dat_dir.mkdir()
        (dat_dir / "sample_msd_data.dat").write_text(
            "# Time(ps) H_MSD(A2) H_RMSD(A)\n"
            "0.0 0.0 0.0\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_batch(self) -> int:
        return run_msd_batch.main(
            [
                "--work-root",
                str(self.work_root),
                "--skip-existing",
                "--with-plot",
            ]
        )

    def test_missing_png_is_generated_from_existing_dat(self) -> None:
        with (
            patch.object(run_msd_batch, "plot_system", return_value=True) as plot,
            patch.object(run_msd_batch, "extract_one") as extract,
        ):
            self.assertEqual(self.run_batch(), 0)

        plot.assert_called_once()
        extract.assert_not_called()

    def test_plot_failure_makes_single_system_batch_fail(self) -> None:
        with patch.object(run_msd_batch, "plot_system", return_value=False):
            self.assertEqual(self.run_batch(), 1)


if __name__ == "__main__":
    unittest.main()
