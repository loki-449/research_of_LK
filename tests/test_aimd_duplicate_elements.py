#!/usr/bin/env python3
"""
验证重复 AIMD 元素选择不会生成或接受列结构损坏的正式 DAT。

基本用法:
  python -m unittest tests/test_aimd_duplicate_elements.py

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / "AIMD" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import compute_msd_by_element, load_dat, write_dat


class AimdDuplicateElementTest(unittest.TestCase):
    """重复元素或重复列必须在正式文件被改写前失败。"""

    def test_compute_rejects_duplicate_elements(self) -> None:
        positions = np.zeros((2, 1, 3))
        with self.assertRaisesRegex(ValueError, "Duplicate elements requested"):
            compute_msd_by_element(
                positions,
                timestep_fs=1.0,
                elem_map=["H"],
                elements=["H", "H"],
            )

    def test_write_rejects_duplicates_without_overwriting_existing_file(self) -> None:
        data = {
            "Time_ps": np.array([0.0, 0.001]),
            "H_MSD": np.array([0.0, 0.1]),
            "H_RMSD": np.array([0.0, 0.1**0.5]),
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "published.dat"
            output.write_text("existing-result\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "Duplicate elements in output order"
            ):
                write_dat(data, output, stride=1, element_order=["H", "H"])

            self.assertEqual(
                output.read_text(encoding="utf-8"), "existing-result\n"
            )

    def test_load_rejects_duplicate_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datafile = Path(tmp) / "duplicate.dat"
            datafile.write_text(
                "# Time(ps) H_MSD(A2) H_MSD(A2)\n"
                "0.0 0.0 0.0\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Duplicate columns"):
                load_dat(datafile)

    def test_load_rejects_rows_with_wrong_column_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datafile = Path(tmp) / "truncated.dat"
            datafile.write_text(
                "# Time(ps) H_MSD(A2) H_RMSD(A)\n"
                "0.0 0.0\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Column count mismatch"):
                load_dat(datafile)


if __name__ == "__main__":
    unittest.main()
