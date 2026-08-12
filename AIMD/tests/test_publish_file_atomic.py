#!/usr/bin/env python3
"""
test_publish_file_atomic.py — AIMD 结果原子发布回归测试。

用途:
  验证复制失败或跨文件系统移动失败时，已有汇总结果不会被删除或截断。

基本用法:
  python3 -m unittest discover -s AIMD/tests -v

参数说明:
  无命令行参数；测试使用临时目录，不读写实际计算数据。
"""
from __future__ import annotations

import errno
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

import msd_common  # noqa: E402


class PublishFileAtomicTests(unittest.TestCase):
    """验证发布失败不会破坏源文件或已有目标文件。"""

    @staticmethod
    def _fail_after_partial_copy(src: Path, dest: Path) -> None:
        Path(dest).write_bytes(b"partial-new-result\n")
        raise OSError("simulated copy failure")

    def test_keep_local_copy_failure_preserves_existing_destination(self) -> None:
        """保留本地结果的复制失败时，旧汇总文件必须保持完整。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "new.dat"
            dest = root / "archive" / "result.dat"
            dest.parent.mkdir()
            src.write_bytes(b"complete-new-result\n")
            dest.write_bytes(b"complete-old-result\n")

            with mock.patch.object(
                msd_common.shutil,
                "copy2",
                side_effect=self._fail_after_partial_copy,
            ):
                with self.assertRaisesRegex(OSError, "simulated copy failure"):
                    msd_common.publish_file(src, dest, keep_local=True)

            self.assertEqual(src.read_bytes(), b"complete-new-result\n")
            self.assertEqual(dest.read_bytes(), b"complete-old-result\n")
            self.assertEqual(list(dest.parent.glob(".result.dat.*.tmp")), [])

    def test_cross_device_copy_failure_preserves_both_files(self) -> None:
        """默认移动跨文件系统且复制失败时，不得先删除旧汇总结果。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "new.dat"
            dest = root / "archive" / "result.dat"
            dest.parent.mkdir()
            src.write_bytes(b"complete-new-result\n")
            dest.write_bytes(b"complete-old-result\n")

            def replace_with_cross_device_error(source: Path, target: Path) -> None:
                if Path(source) == src:
                    raise OSError(errno.EXDEV, "simulated cross-device move")
                raise AssertionError("copy failure should occur before temp replacement")

            with (
                mock.patch.object(
                    msd_common.os,
                    "replace",
                    side_effect=replace_with_cross_device_error,
                ),
                mock.patch.object(
                    msd_common.shutil,
                    "copy2",
                    side_effect=self._fail_after_partial_copy,
                ),
            ):
                with self.assertRaisesRegex(OSError, "simulated copy failure"):
                    msd_common.publish_file(src, dest)

            self.assertEqual(src.read_bytes(), b"complete-new-result\n")
            self.assertEqual(dest.read_bytes(), b"complete-old-result\n")
            self.assertEqual(list(dest.parent.glob(".result.dat.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
