#!/usr/bin/env python3
"""
test_incar_parsing.py — AIMD INCAR 时间步解析回归测试。

用途:
  验证 POTIM 可从合法的 VASP 分号分隔标签中读取，避免批处理在解析阶段崩溃。

基本用法:
  python3 -m unittest AIMD/tests/test_incar_parsing.py -v

参数说明:
  无。测试仅使用临时文件，不读写实际计算数据。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import read_potim_from_incar  # noqa: E402


class IncarParsingTests(unittest.TestCase):
    """验证 INCAR 实数及标签分隔符解析。"""

    def test_potim_before_semicolon_is_parsed(self) -> None:
        """同一行存在后续 INCAR 标签时，POTIM 不应包含分号。"""
        with tempfile.TemporaryDirectory() as tmp:
            incar = Path(tmp) / "INCAR"
            incar.write_text(
                "POTIM = 0.5; NBLOCK = 10\n",
                encoding="utf-8",
            )

            self.assertEqual(read_potim_from_incar(incar), 0.5)

    def test_fortran_exponent_is_parsed(self) -> None:
        """兼容 VASP 输入中常见的 Fortran 双精度指数写法。"""
        with tempfile.TemporaryDirectory() as tmp:
            incar = Path(tmp) / "INCAR"
            incar.write_text("POTIM = 5D-1\n", encoding="utf-8")

            self.assertEqual(read_potim_from_incar(incar), 0.5)


if __name__ == "__main__":
    unittest.main()
