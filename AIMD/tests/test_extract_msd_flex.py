#!/usr/bin/env python3
"""
用途：验证单体系 MSD 提取入口遵循工作根路径优先级。

基本用法：
  python -m unittest AIMD/tests/test_extract_msd_flex.py

参数说明：
  本测试脚本无命令行参数，使用临时目录且不读写真实计算数据。
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "MSD_RMSD"
sys.path.insert(0, str(SCRIPT_DIR))

import extract_msd_flex


class ExtractMsdWorkRootTests(unittest.TestCase):
    """覆盖单体系入口的 AIMD_WORK_ROOT 解析。"""

    def test_single_file_mode_uses_environment_work_root(self) -> None:
        """未传 --work-root 时应使用 AIMD_WORK_ROOT，而非输入文件父目录。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            configured_root = root / "configured"
            xdatcar = root / "other" / "Sample" / "AIMD" / "XDATCAR"
            configured_root.mkdir()
            xdatcar.parent.mkdir(parents=True)
            xdatcar.touch()

            with mock.patch.dict(
                os.environ, {"AIMD_WORK_ROOT": str(configured_root)}
            ), mock.patch.object(
                extract_msd_flex, "extract_one", return_value=True
            ) as extract_one:
                result = extract_msd_flex.main([str(xdatcar), "--dry-run"])

            self.assertEqual(result, 0)
            self.assertEqual(extract_one.call_args.args[1], configured_root.resolve())


if __name__ == "__main__":
    unittest.main()
