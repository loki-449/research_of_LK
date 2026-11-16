#!/usr/bin/env python3
"""
AIMD 批处理体系级异常隔离回归测试。

用途:
  验证前一个体系的 XDATCAR 损坏时，批量入口仍会处理并发布后续合法体系。

基本用法:
  python -m unittest tests/test_aimd_batch_exception_isolation.py

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AIMD_SCRIPT_DIR = REPO_ROOT / "AIMD" / "scripts" / "MSD_RMSD"
sys.path.insert(0, str(AIMD_SCRIPT_DIR))

from extract_msd_flex import main as extract_main
from run_msd_batch import main as batch_main


VALID_XDATCAR = """test
1.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H
1
Direct configuration=     1
0.0 0.0 0.0
Direct configuration=     2
0.1 0.0 0.0
"""

BROKEN_XDATCAR = VALID_XDATCAR.replace("0.0 0.0 0.0", "BROKEN 0.0 0.0", 1)


class BatchExceptionIsolationTest(unittest.TestCase):
    """损坏体系不能阻止同一批次中的后续合法体系。"""

    @staticmethod
    def _add_system(work_root: Path, name: str, xdatcar: str) -> None:
        aimd_dir = work_root / name / "AIMD"
        aimd_dir.mkdir(parents=True)
        (aimd_dir / "INCAR").write_text("POTIM = 1.0\n", encoding="utf-8")
        (aimd_dir / "XDATCAR").write_text(xdatcar, encoding="utf-8")

    def test_both_batch_entries_continue_after_broken_xdatcar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            self._add_system(work_root, "00-broken", BROKEN_XDATCAR)
            self._add_system(work_root, "01-valid", VALID_XDATCAR)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                extract_main(
                    [
                        "--scan",
                        "--work-root",
                        str(work_root),
                        "--stride",
                        "1",
                        "--no-publish",
                    ]
                )

            self.assertIn("ERROR:", output.getvalue())
            self.assertTrue((work_root / "01-valid" / "msd_data.dat").is_file())

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                batch_main(
                    [
                        "--work-root",
                        str(work_root),
                        "--stride",
                        "1",
                    ]
                )

            self.assertIn("ERROR:", output.getvalue())
            self.assertTrue(
                (
                    work_root
                    / "MSD_data_for_origin"
                    / "01-valid_msd_data.dat"
                ).is_file()
            )


if __name__ == "__main__":
    unittest.main()
