#!/usr/bin/env python3
"""
验证 XDATCAR 计数行与每帧坐标行数必须一致。

用途:
  防止计数总和小于实际原子数时，解析器静默丢弃多余坐标并错标元素 MSD。

基本用法:
  python3 -m unittest AIMD/tests/test_msd_atom_counts.py -v

参数说明:
  无；测试使用临时 XDATCAR，不读写真实计算结果。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import read_xdatcar  # noqa: E402


class XdatcarAtomCountTests(unittest.TestCase):
    """覆盖计数准确与少计时的解析行为。"""

    @staticmethod
    def _write_xdatcar(root: Path, counts: str) -> Path:
        path = root / "XDATCAR"
        path.write_text(
            f"""atom-count validation
1.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H Ag
{counts}
Direct configuration=     1
0.0 0.0 0.0
0.1 0.0 0.0
0.5 0.5 0.5
Direct configuration=     2
0.0 0.0 0.0
0.2 0.0 0.0
0.6 0.5 0.5
""",
            encoding="utf-8",
        )
        return path

    def test_rejects_frame_with_more_coordinates_than_atom_counts(self) -> None:
        """少计一个 H 时不得把第二个 H 静默当作 Ag。"""
        with tempfile.TemporaryDirectory() as tmp:
            xdatcar = self._write_xdatcar(Path(tmp), counts="1 1")

            with self.assertRaisesRegex(
                ValueError,
                r"Frame 1 .* contains more than 2 coordinate rows",
            ):
                read_xdatcar(xdatcar)

    def test_accepts_frame_matching_atom_counts(self) -> None:
        """计数总和与每帧坐标数一致时保持正常解析。"""
        with tempfile.TemporaryDirectory() as tmp:
            xdatcar = self._write_xdatcar(Path(tmp), counts="2 1")

            positions, elem_map = read_xdatcar(xdatcar)

        self.assertEqual(positions.shape, (2, 3, 3))
        self.assertEqual(elem_map, ["H", "H", "Ag"])

    def test_accepts_numeric_comment_in_repeated_variable_cell_header(self) -> None:
        """逐帧重复头的自由注释即使是三个数字也不是额外原子坐标。"""
        content = """1 2 3
1.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H
1
Direct configuration=     1
0.0 0.0 0.0
4 5 6
1.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H
1
Direct configuration=     2
0.1 0.0 0.0
"""
        with tempfile.TemporaryDirectory() as tmp:
            xdatcar = Path(tmp) / "XDATCAR"
            xdatcar.write_text(content, encoding="utf-8")

            positions, elem_map = read_xdatcar(xdatcar)

        self.assertEqual(positions.shape, (2, 1, 3))
        self.assertEqual(elem_map, ["H"])


if __name__ == "__main__":
    unittest.main()
