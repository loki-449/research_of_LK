#!/usr/bin/env python3
"""
test_msd_common.py — AIMD MSD 公共文件操作的回归测试

用途:
  验证发布产物时不会删除已位于汇总目标的文件。

基本用法:
  python -m unittest discover -s AIMD/tests
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import publish_file


class PublishFileTests(unittest.TestCase):
    def test_same_source_and_destination_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "MSD_data_for_origin" / "sample_msd_data.dat"
            target.parent.mkdir()
            target.write_text("scientific result\n", encoding="utf-8")

            for keep_local in (False, True):
                with self.subTest(keep_local=keep_local):
                    result = publish_file(target, target, keep_local=keep_local)
                    self.assertEqual(result, target)
                    self.assertEqual(
                        target.read_text(encoding="utf-8"), "scientific result\n"
                    )

    def test_equivalent_paths_are_treated_as_same_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "archive" / "sample.dat"
            target.parent.mkdir()
            target.write_text("preserve me\n", encoding="utf-8")
            equivalent = root / "archive" / ".." / "archive" / "sample.dat"

            publish_file(target, equivalent)

            self.assertTrue(target.is_file())
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve me\n")


if __name__ == "__main__":
    unittest.main()
