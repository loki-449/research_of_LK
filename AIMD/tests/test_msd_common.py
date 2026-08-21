#!/usr/bin/env python3
"""
test_msd_common.py — AIMD XDATCAR 解析回归测试。

用途:
  验证固定晶格与 NpT 逐帧晶格均按 XDATCAR 头正确换算为笛卡尔坐标。

基本用法:
  python3 -m unittest AIMD/tests/test_msd_common.py -v

参数说明:
  无命令行参数；测试使用临时目录构造最小 XDATCAR。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import compute_msd_by_element, read_xdatcar  # noqa: E402


class ReadXdatcarLatticeTests(unittest.TestCase):
    """验证每个轨迹帧使用与其对应的晶格。"""

    def test_npt_repeated_header_updates_frame_lattice(self) -> None:
        """晶胞变化时，相同分数坐标必须映射到不同笛卡尔位置。"""
        content = """Direct-coordinate NpT frame 1
1.0
10.0 0.0 0.0
0.0 10.0 0.0
0.0 0.0 10.0
H
1
Direct configuration=     1
0.5 0.0 0.0
Direct-coordinate NpT frame 2
1.0
12.0 0.0 0.0
0.0 12.0 0.0
0.0 0.0 12.0
H
1
Direct configuration=     2
0.5 0.0 0.0
"""
        with tempfile.TemporaryDirectory() as tmp:
            xdatcar = Path(tmp) / "XDATCAR"
            xdatcar.write_text(content, encoding="utf-8")

            positions, elem_map = read_xdatcar(xdatcar)
            results = compute_msd_by_element(positions, 1.0, elem_map)

        self.assertEqual(positions[:, 0, 0].tolist(), [5.0, 6.0])
        self.assertEqual(results["H"][1].tolist(), [0.0, 1.0])

    def test_nvt_frames_continue_to_share_initial_lattice(self) -> None:
        """固定晶格的紧凑 XDATCAR 不应被误识别为重复头格式。"""
        content = """NVT trajectory
1.0
10.0 0.0 0.0
0.0 10.0 0.0
0.0 0.0 10.0
H
1
Direct
0.1 0.0 0.0
Direct
0.2 0.0 0.0
"""
        with tempfile.TemporaryDirectory() as tmp:
            xdatcar = Path(tmp) / "XDATCAR"
            xdatcar.write_text(content, encoding="utf-8")
            positions, _ = read_xdatcar(xdatcar)

        self.assertEqual(positions[:, 0, 0].tolist(), [1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
