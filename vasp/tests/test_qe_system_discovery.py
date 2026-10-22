#!/usr/bin/env python3
"""
test_qe_system_discovery.py — QE 体系扫描边界回归测试。

用途:
  验证自定义 glob 只能返回 QE 输入根目录内的体系，不能通过 ``..``
  或符号链接扫描并部署根目录外的数据。

基本用法:
  python3 -m unittest vasp/tests/test_qe_system_discovery.py -v

参数说明:
  无。测试仅使用标准库与临时目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import find_qe_system_dirs  # noqa: E402


class QeSystemDiscoveryBoundaryTests(unittest.TestCase):
    """验证扫描结果始终位于调用者指定的 QE 根目录内。"""

    def test_parent_pattern_cannot_scan_sibling_systems(self) -> None:
        """包含 ``..`` 的 pattern 不得返回 QE 根目录的同级体系。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            qe_root = parent / "campaign"
            qe_root.mkdir()
            sibling = parent / "outside-H-50GPa-300K"
            sibling.mkdir()

            matches = find_qe_system_dirs(qe_root, "../*GPa*")

            self.assertEqual(matches, [])

    def test_normal_pattern_still_finds_child_systems(self) -> None:
        """合法 pattern 应保持原有的根内目录发现行为。"""
        with tempfile.TemporaryDirectory() as tmp:
            qe_root = Path(tmp)
            expected = qe_root / "Ag-H-50GPa-300K"
            expected.mkdir()

            matches = find_qe_system_dirs(qe_root)

            self.assertEqual(matches, [expected])

    def test_symlink_cannot_escape_qe_root(self) -> None:
        """根内指向外部体系的符号链接不得绕过边界检查。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            qe_root = parent / "campaign"
            qe_root.mkdir()
            outside = parent / "outside-H-50GPa-300K"
            outside.mkdir()
            link = qe_root / "linked-H-50GPa-300K"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"当前文件系统不支持符号链接: {exc}")

            matches = find_qe_system_dirs(qe_root)

            self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
