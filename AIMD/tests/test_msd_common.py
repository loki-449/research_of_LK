"""测试 AIMD MSD 公共模块中的时间步长解析。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from msd_common import read_nblock_from_incar, resolve_dt


class ResolveDtTests(unittest.TestCase):
    """验证 XDATCAR 帧间隔包含 VASP 的输出步长 NBLOCK。"""

    def make_aimd_dir(self, incar_text: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        aimd_dir = Path(temp_dir.name)
        (aimd_dir / "INCAR").write_text(incar_text, encoding="utf-8")
        return aimd_dir

    def test_resolve_dt_multiplies_potim_by_nblock(self) -> None:
        aimd_dir = self.make_aimd_dir("POTIM = 0.5\nNBLOCK = 10\n")

        dt_fs, source = resolve_dt(aimd_dir)

        self.assertEqual(dt_fs, 5.0)
        self.assertIn("NBLOCK=10", source)

    def test_resolve_dt_uses_vasp_default_nblock(self) -> None:
        aimd_dir = self.make_aimd_dir("POTIM = 2.0\n")

        dt_fs, source = resolve_dt(aimd_dir)

        self.assertEqual(dt_fs, 2.0)
        self.assertIn("NBLOCK=1", source)

    def test_read_nblock_rejects_non_positive_value(self) -> None:
        aimd_dir = self.make_aimd_dir("POTIM = 1.0\nNBLOCK = 0\n")

        with self.assertRaisesRegex(ValueError, "positive integer"):
            read_nblock_from_incar(aimd_dir / "INCAR")


if __name__ == "__main__":
    unittest.main()
