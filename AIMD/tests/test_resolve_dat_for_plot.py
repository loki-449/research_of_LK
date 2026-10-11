#!/usr/bin/env python3
"""
用途：验证 MSD 绘图数据文件解析不会忽略无效的显式输入路径。

基本用法：
  python3 -m unittest AIMD/tests/test_resolve_dat_for_plot.py -v

参数说明：
  无命令行参数；测试仅在临时目录中创建占位数据文件。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from msd_common import published_dat_path, resolve_dat_for_plot  # noqa: E402


class ResolveDatForPlotTests(unittest.TestCase):
    """覆盖显式输入和默认归档查找的优先级。"""

    def test_missing_explicit_file_does_not_fall_back_to_archive(self) -> None:
        """显式文件不存在时，即使归档存在也必须报错。"""
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            archive = published_dat_path(work_root, "system-a")
            archive.parent.mkdir(parents=True)
            archive.write_text("archived data\n", encoding="utf-8")

            missing = work_root / "requested.dat"
            with self.assertRaisesRegex(
                FileNotFoundError, "Data file not found"
            ):
                resolve_dat_for_plot(work_root, "system-a", missing)

    def test_empty_explicit_path_does_not_fall_back_to_archive(self) -> None:
        """显式空路径也不能被误当作未提供参数。"""
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            archive = published_dat_path(work_root, "system-a")
            archive.parent.mkdir(parents=True)
            archive.write_text("archived data\n", encoding="utf-8")

            with self.assertRaisesRegex(
                FileNotFoundError, "Data file not found"
            ):
                resolve_dat_for_plot(work_root, "system-a", "")

    def test_existing_explicit_file_takes_precedence_over_archive(self) -> None:
        """显式文件有效时始终使用该文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            archive = published_dat_path(work_root, "system-a")
            archive.parent.mkdir(parents=True)
            archive.write_text("archived data\n", encoding="utf-8")
            requested = work_root / "requested.dat"
            requested.write_text("requested data\n", encoding="utf-8")

            self.assertEqual(
                resolve_dat_for_plot(work_root, "system-a", requested),
                requested,
            )

    def test_archive_is_used_when_no_explicit_file_is_given(self) -> None:
        """未指定文件时保留原有的归档查找行为。"""
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            archive = published_dat_path(work_root, "system-a")
            archive.parent.mkdir(parents=True)
            archive.write_text("archived data\n", encoding="utf-8")

            self.assertEqual(
                resolve_dat_for_plot(work_root, "system-a", None),
                archive,
            )


if __name__ == "__main__":
    unittest.main()
