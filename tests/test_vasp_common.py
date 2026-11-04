#!/usr/bin/env python3
"""
test_vasp_common.py — VASP 公共解析模块回归测试

用途:
  验证 QE relax.in 的结构解析不会把后续卡片内容误作晶格矢量。

基本用法:
  python -m unittest discover -s tests -p 'test_*.py'

参数说明:
  无命令行参数；测试通过 unittest 自动发现执行。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "vasp" / "scripts" / "lib"))

from vasp_common import parse_relax_in


class ParseRelaxInCellTests(unittest.TestCase):
    """检查 CELL_PARAMETERS 与后续 QE 卡片的边界。"""

    def parse_text(self, text: str):
        """将最小 relax.in 文本写入临时文件并解析。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            relax_in = Path(tmpdir) / "relax.in"
            relax_in.write_text(text, encoding="utf-8")
            return parse_relax_in(relax_in)

    def test_rejects_k_point_grid_as_third_cell_vector(self) -> None:
        """晶格少一行时必须报错，不能吞入 K 点网格。"""
        text = """\
CELL_PARAMETERS angstrom
10.0 0.0 0.0
0.0 10.0 0.0
K_POINTS automatic
1 1 1 0 0 0
ATOMIC_POSITIONS crystal
H 0.0 0.0 0.0
"""
        with self.assertRaisesRegex(ValueError, "Invalid cell vector"):
            self.parse_text(text)

    def test_accepts_three_numeric_cell_vectors(self) -> None:
        """完整的三条数值晶格矢量应保持可解析。"""
        text = """\
CELL_PARAMETERS { angstrom }
10.0 0.0 0.0
0.0 10.0 0.0
0.0 0.0 10.0
K_POINTS automatic
1 1 1 0 0 0
ATOMIC_POSITIONS crystal
H 0.0 0.0 0.0
"""
        structure = self.parse_text(text)
        self.assertEqual(
            structure.cell_lines,
            ["10.0 0.0 0.0", "0.0 10.0 0.0", "0.0 0.0 10.0"],
        )


if __name__ == "__main__":
    unittest.main()
