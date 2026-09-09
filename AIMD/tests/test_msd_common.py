#!/usr/bin/env python3
"""
test_msd_common.py — 验证 XDATCAR 解析的结构一致性检查。

基本用法:
  python -m unittest AIMD/tests/test_msd_common.py

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import read_xdatcar


class ReadXdatcarTests(unittest.TestCase):
    """测试 XDATCAR 头信息与原子映射的一致性。"""

    def test_rejects_element_count_column_mismatch(self) -> None:
        cases = (
            ("H Ag Ba", "2 1"),
            ("H Ag", "2 1 1"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            for index, (elements, counts) in enumerate(cases):
                path = Path(tmp) / f"XDATCAR.{index}"
                path.write_text(
                    "\n".join(
                        (
                            "test",
                            "1.0",
                            "1 0 0",
                            "0 1 0",
                            "0 0 1",
                            elements,
                            counts,
                        )
                    )
                    + "\n",
                    encoding="utf-8",
                )
                with self.subTest(elements=elements, counts=counts):
                    with self.assertRaisesRegex(
                        ValueError, "Element/count column mismatch"
                    ):
                        read_xdatcar(path)


if __name__ == "__main__":
    unittest.main()
