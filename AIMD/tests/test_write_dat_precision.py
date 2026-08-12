#!/usr/bin/env python3
"""
test_write_dat_precision.py — AIMD 数值导出精度回归测试。

用途:
  验证微小但非零的 MSD 写入数据表后不会被静默舍入为零。

基本用法:
  python3 -m unittest discover -s AIMD/tests -v

参数说明:
  无命令行参数；测试使用临时目录，不读写实际计算数据。
"""
from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import load_dat, write_dat  # noqa: E402


class WriteDatPrecisionTests(unittest.TestCase):
    """验证 MSD/RMSD 小量导出后仍保留物理关系。"""

    def test_small_nonzero_msd_survives_round_trip(self) -> None:
        """低于固定六位小数阈值的 MSD 不得被写成零。"""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "msd.dat"
            data = {
                "Time_ps": [0.0, 0.0005],
                "H_MSD": [0.0, 4.0e-12],
                "H_RMSD": [0.0, 2.0e-6],
            }

            write_dat(data, output, stride=1, element_order=["H"])
            loaded = load_dat(output)

            msd = loaded["H_MSD(A2)"][1]
            rmsd = loaded["H_RMSD(A)"][1]
            self.assertGreater(msd, 0.0)
            self.assertGreater(rmsd, 0.0)
            self.assertTrue(
                math.isclose(rmsd, math.sqrt(msd), rel_tol=1.0e-9),
                f"RMSD={rmsd} 与 sqrt(MSD)={math.sqrt(msd)} 不一致",
            )


if __name__ == "__main__":
    unittest.main()
