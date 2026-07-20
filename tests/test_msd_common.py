"""AIMD MSD 公共模块的回归测试。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

LIB_DIR = Path(__file__).resolve().parents[1] / "AIMD" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import write_dat


class WriteDatTests(unittest.TestCase):
    """验证 MSD 数据写出不会破坏已有结果。"""

    def test_non_positive_stride_does_not_truncate_existing_output(self) -> None:
        data = {
            "Time_ps": np.array([0.0, 0.1]),
            "H_MSD": np.array([0.0, 1.0]),
            "H_RMSD": np.array([0.0, 1.0]),
        }

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "existing.dat"
            original = "validated result\n"

            for stride in (0, -1):
                with self.subTest(stride=stride):
                    output.write_text(original, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "stride must be >= 1"):
                        write_dat(data, output, stride=stride, element_order=["H"])
                    self.assertEqual(output.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
