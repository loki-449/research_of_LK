#!/usr/bin/env python3
"""
test_msd_common.py — 验证 MSD/RMSD 公共模块的数据抽样行为。

基本用法:
  python -m unittest AIMD/tests/test_msd_common.py

参数说明:
  本测试脚本不接收命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import write_dat


class WriteDatTests(unittest.TestCase):
    """验证抽样输出不会静默丢失轨迹末帧。"""

    @staticmethod
    def make_data(n_frames: int) -> dict[str, list[float]]:
        values = [float(i) for i in range(n_frames)]
        return {
            "Time_ps": [value / 1000.0 for value in values],
            "H_MSD": values,
            "H_RMSD": [value**0.5 for value in values],
        }

    def write_and_read_rows(self, n_frames: int, stride: int) -> list[list[float]]:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "msd.dat"
            write_dat(
                self.make_data(n_frames),
                output,
                stride=stride,
                element_order=["H"],
            )
            lines = output.read_text(encoding="utf-8").splitlines()[1:]
        return [[float(value) for value in line.split()] for line in lines]

    def test_stride_larger_than_trajectory_keeps_final_frame(self) -> None:
        rows = self.write_and_read_rows(n_frames=5, stride=100)

        self.assertEqual([row[1] for row in rows], [0.0, 4.0])

    def test_aligned_final_frame_is_not_duplicated(self) -> None:
        rows = self.write_and_read_rows(n_frames=201, stride=100)

        self.assertEqual([row[1] for row in rows], [0.0, 100.0, 200.0])

    def test_unaligned_final_frame_is_appended(self) -> None:
        rows = self.write_and_read_rows(n_frames=250, stride=100)

        self.assertEqual([row[1] for row in rows], [0.0, 100.0, 200.0, 249.0])


if __name__ == "__main__":
    unittest.main()
