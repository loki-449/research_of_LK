#!/usr/bin/env python3
"""
test_submit_opt.py — submit_opt 提交前输入完整性回归测试

基本用法:
  python -m unittest vasp/tests/test_submit_opt.py

覆盖参数:
  无命令行参数；测试通过临时工作目录构造 opt.pbs、POSCAR 与 POTCAR。
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Tuple


OPT_SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "opt"
sys.path.insert(0, str(OPT_SCRIPT_DIR))

import submit_opt


class SubmitOptInputValidationTests(unittest.TestCase):
    def make_opt_dir(
        self,
        root: Path,
        material: str,
        pressure: str,
        complete: bool,
    ) -> Path:
        opt_dir = root / material / pressure / "opt"
        opt_dir.mkdir(parents=True)
        (opt_dir / "opt.pbs").write_text("#!/bin/bash\n", encoding="utf-8")
        if complete:
            (opt_dir / "POSCAR").write_text("structure\n", encoding="utf-8")
            (opt_dir / "POTCAR").write_text("potential\n", encoding="utf-8")
        return opt_dir

    def run_submit(
        self,
        work_root: Path,
        *,
        resubmit: bool = False,
        clear_only: bool = False,
        dry_run: bool = True,
    ) -> Tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = submit_opt.submit_all(
                work_root,
                max_jobs=8,
                wait_interval=1,
                no_wait=True,
                resubmit=resubmit,
                clear_only=clear_only,
                dry_run=dry_run,
            )
        return status, output.getvalue()

    def test_incomplete_input_set_aborts_before_any_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_opt_dir(root, "Ag", "50", complete=True)
            incomplete = self.make_opt_dir(root, "La", "100", complete=False)
            (incomplete / "POSCAR").write_text("structure\n", encoding="utf-8")
            (incomplete / "POTCAR").touch()

            status, output = self.run_submit(root)

            self.assertEqual(status, 1)
            self.assertIn("submission aborted", output)
            self.assertIn("missing or empty POTCAR", output)
            self.assertNotIn("SUBMITTED", output)
            self.assertFalse((incomplete / submit_opt.MARKER_NAME).exists())

    def test_complete_input_set_can_be_submitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_opt_dir(root, "Ag", "50", complete=True)

            status, output = self.run_submit(root)

            self.assertEqual(status, 0)
            self.assertIn("[dry-run] qsub", output)
            self.assertIn("SUBMITTED", output)

    def test_already_submitted_directory_does_not_block_new_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_dir = self.make_opt_dir(root, "Ag", "50", complete=False)
            (old_dir / submit_opt.MARKER_NAME).write_text(
                "job_id=123.server\n", encoding="utf-8"
            )
            self.make_opt_dir(root, "La", "100", complete=True)

            status, output = self.run_submit(root)

            self.assertEqual(status, 0)
            self.assertIn("SKIP: already submitted", output)
            self.assertIn("SUBMITTED", output)

    def test_failed_resubmit_preflight_preserves_existing_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            opt_dir = self.make_opt_dir(root, "Ag", "50", complete=False)
            marker = opt_dir / submit_opt.MARKER_NAME
            marker.write_text("job_id=123.server\n", encoding="utf-8")

            status, output = self.run_submit(root, resubmit=True)

            self.assertEqual(status, 1)
            self.assertIn("submission aborted", output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "job_id=123.server\n")

    def test_dry_run_resubmit_does_not_delete_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            opt_dir = self.make_opt_dir(root, "Ag", "50", complete=True)
            marker = opt_dir / submit_opt.MARKER_NAME
            marker.write_text("job_id=123.server\n", encoding="utf-8")

            status, output = self.run_submit(root, resubmit=True)

            self.assertEqual(status, 0)
            self.assertIn("[dry-run] would clear", output)
            self.assertTrue(marker.is_file())


if __name__ == "__main__":
    unittest.main()
