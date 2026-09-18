#!/usr/bin/env python3
"""验证 MSD 提取不会用输出文件覆盖原始 XDATCAR。

基本用法:
  python3 -m unittest AIMD/tests/test_extract_msd_flex.py

参数说明:
  无命令行参数；测试使用临时目录，不修改真实计算数据。
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "MSD_RMSD"
sys.path.insert(0, str(SCRIPT_DIR))

import extract_msd_flex
from extract_msd_flex import extract_one


class ExtractOutputSafetyTest(unittest.TestCase):
    """覆盖输出路径与输入轨迹发生别名的场景。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.system_dir = Path(self.temp_dir.name) / "sample"
        self.aimd_dir = self.system_dir / "AIMD"
        self.aimd_dir.mkdir(parents=True)
        self.xdatcar = self.aimd_dir / "XDATCAR"
        self.original = (
            b"test\n1.0\n1 0 0\n0 1 0\n0 0 1\nH\n1\n"
            b"Direct configuration= 1\n0 0 0\n"
            b"Direct configuration= 2\n0.1 0 0\n"
        )
        self.xdatcar.write_bytes(self.original)
        (self.aimd_dir / "INCAR").write_text("POTIM = 1.0\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_extract(self, output: Path) -> bool:
        """以指定输出路径调用单体系提取入口。"""
        with contextlib.redirect_stdout(io.StringIO()):
            return extract_one(
                self.xdatcar,
                self.system_dir.parent,
                None,
                output,
                1,
                None,
                "file",
                False,
                True,
                False,
            )

    def test_rejects_input_path_as_output(self) -> None:
        self.assertFalse(self.run_extract(self.xdatcar))
        self.assertEqual(self.xdatcar.read_bytes(), self.original)

    def test_rejects_hard_link_to_input_as_output(self) -> None:
        alias = self.aimd_dir / "output.dat"
        os.link(self.xdatcar, alias)

        self.assertFalse(self.run_extract(alias))
        self.assertEqual(self.xdatcar.read_bytes(), self.original)

    def test_rejects_symbolic_link_to_input_as_output(self) -> None:
        alias = self.aimd_dir / "output.dat"
        alias.symlink_to(self.xdatcar)

        self.assertFalse(self.run_extract(alias))
        self.assertEqual(self.xdatcar.read_bytes(), self.original)

    def test_rechecks_open_file_before_truncating_output(self) -> None:
        output = self.system_dir / "output.dat"
        output.write_text("safe output\n", encoding="utf-8")
        real_read = extract_msd_flex.read_xdatcar

        def read_then_swap(path: Path, stream=None):
            result = real_read(path, stream=stream)
            output.unlink()
            os.link(self.xdatcar, output)
            decoy = self.aimd_dir / "decoy"
            decoy.write_text("replacement path\n", encoding="utf-8")
            self.xdatcar.unlink()
            decoy.rename(self.xdatcar)
            return result

        with mock.patch.object(
            extract_msd_flex, "read_xdatcar", side_effect=read_then_swap
        ):
            self.assertFalse(self.run_extract(output))

        self.assertEqual(output.read_bytes(), self.original)
        self.assertEqual(self.xdatcar.read_bytes(), b"replacement path\n")

    def test_allows_distinct_output_file(self) -> None:
        output = self.system_dir / "output.dat"

        self.assertTrue(self.run_extract(output))
        self.assertTrue(output.read_text(encoding="utf-8").startswith("#"))
        self.assertEqual(self.xdatcar.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
