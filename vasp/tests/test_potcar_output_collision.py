#!/usr/bin/env python3
"""
test_potcar_output_collision.py — POTCAR 输出与中间文件冲突回归测试。

基本用法:
  python3 -m unittest vasp/tests/test_potcar_output_collision.py -v

参数说明:
  无命令行参数；测试仅使用标准库和临时目录。
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import assemble_potcar  # noqa: E402


class PotcarOutputCollisionTests(unittest.TestCase):
    """验证正式输出不会与 <Elem>.POTCAR 中间文件互相覆盖。"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        source = self.root / "pbe" / "H" / "POTCAR"
        source.parent.mkdir(parents=True)
        source.write_text(
            "PAW_PBE H 01Jan2020\nZVAL = 1.0\n",
            encoding="utf-8",
        )
        self.out_dir = self.root / "work"
        self.out_dir.mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_element_named_output_is_rejected_before_overwrite(self) -> None:
        """显式 H.POTCAR 输出必须保留已有文件并报告失败。"""
        output = self.out_dir / "H.POTCAR"
        original = b"existing result\n"
        output.write_bytes(original)

        with self.assertRaisesRegex(ValueError, "conflicts with intermediate"):
            assemble_potcar(["H"], output, pbe_lib=self.root / "pbe")

        self.assertEqual(output.read_bytes(), original)

    def test_symlink_alias_is_rejected_before_overwrite(self) -> None:
        """不同名称的输出链接到 H.POTCAR 时也必须在写入前失败。"""
        single = self.out_dir / "H.POTCAR"
        original = b"existing result\n"
        single.write_bytes(original)
        output = self.out_dir / "custom.POTCAR"
        try:
            output.symlink_to(single.name)
        except OSError as exc:
            self.skipTest(f"当前文件系统不支持符号链接: {exc}")

        with self.assertRaisesRegex(ValueError, "conflicts with intermediate"):
            assemble_potcar(["H"], output, pbe_lib=self.root / "pbe")

        self.assertEqual(single.read_bytes(), original)
        self.assertTrue(output.is_symlink())

    def test_dangling_symlink_alias_is_rejected_before_copy(self) -> None:
        """悬空输出链接不能在中间文件创建后变成破坏性别名。"""
        single = self.out_dir / "H.POTCAR"
        output = self.out_dir / "custom.POTCAR"
        try:
            output.symlink_to(single.name)
        except OSError as exc:
            self.skipTest(f"当前文件系统不支持符号链接: {exc}")

        with self.assertRaisesRegex(ValueError, "conflicts with intermediate"):
            assemble_potcar(["H"], output, pbe_lib=self.root / "pbe")

        self.assertFalse(single.exists())
        self.assertTrue(output.is_symlink())

    def test_hardlink_alias_is_rejected_before_overwrite(self) -> None:
        """硬链接输出必须通过 inode 一致性识别并保留原文件。"""
        single = self.out_dir / "H.POTCAR"
        original = b"existing result\n"
        single.write_bytes(original)
        output = self.out_dir / "custom.POTCAR"
        try:
            os.link(single, output)
        except OSError as exc:
            self.skipTest(f"当前文件系统不支持硬链接: {exc}")

        with self.assertRaisesRegex(ValueError, "conflicts with intermediate"):
            assemble_potcar(["H"], output, pbe_lib=self.root / "pbe")

        self.assertEqual(single.read_bytes(), original)
        self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
