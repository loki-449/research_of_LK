#!/usr/bin/env python3
"""
AIMD 批量入口退出码回归测试。

用途:
  验证批量扫描仅在全部体系处理成功时返回退出码 0。

基本用法:
  python -m unittest tests/test_aimd_batch_exit_codes.py

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AIMD_SCRIPT_DIR = REPO_ROOT / "AIMD" / "scripts" / "MSD_RMSD"
sys.path.insert(0, str(AIMD_SCRIPT_DIR))

from extract_msd_flex import main as extract_main
from run_msd_batch import main as batch_main


class BatchExitCodeTest(unittest.TestCase):
    """检查完整成功与部分失败对应的退出码。"""

    @staticmethod
    def _add_system(work_root: Path, name: str, with_potim: bool) -> None:
        aimd_dir = work_root / name / "AIMD"
        aimd_dir.mkdir(parents=True)
        (aimd_dir / "XDATCAR").touch()
        if with_potim:
            (aimd_dir / "INCAR").write_text("POTIM = 1.0\n", encoding="utf-8")

    def _assert_exit_codes(self, work_root: Path, expected: int) -> None:
        args = ["--work-root", str(work_root), "--dry-run"]
        self.assertEqual(extract_main(["--scan", *args]), expected)
        self.assertEqual(batch_main(args), expected)

    def test_all_systems_succeed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            self._add_system(work_root, "complete", with_potim=True)
            self._assert_exit_codes(work_root, expected=0)

    def test_partial_failure_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            self._add_system(work_root, "complete", with_potim=True)
            self._add_system(work_root, "missing-potim", with_potim=False)
            self._assert_exit_codes(work_root, expected=1)


if __name__ == "__main__":
    unittest.main()
