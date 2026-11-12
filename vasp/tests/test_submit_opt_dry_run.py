#!/usr/bin/env python3
"""验证 submit_opt 的 dry-run 不会删除防重复提交标记。"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR / "lib"))
sys.path.insert(0, str(SCRIPTS_DIR / "opt"))

import submit_opt  # noqa: E402


class SubmitOptDryRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.work_root = Path(self.temp_dir.name) / "calc"
        self.opt_dir = self.work_root / "Ag" / "50" / "opt"
        self.opt_dir.mkdir(parents=True)
        (self.opt_dir / submit_opt.OPT_PBS_SCRIPT).write_text(
            "#!/bin/bash\n", encoding="utf-8"
        )
        self.marker = self.opt_dir / submit_opt.MARKER_NAME
        self.marker_content = "job_id=123.server\n"
        self.marker.write_text(self.marker_content, encoding="utf-8")

    def run_main(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = submit_opt.main([str(self.work_root), *args])
        return result, output.getvalue()

    def assert_marker_unchanged(self) -> None:
        self.assertTrue(self.marker.is_file())
        self.assertEqual(
            self.marker.read_text(encoding="utf-8"), self.marker_content
        )

    def test_resubmit_dry_run_preserves_existing_marker(self) -> None:
        result, output = self.run_main("--resubmit", "--dry-run")

        self.assertEqual(result, 0)
        self.assert_marker_unchanged()
        self.assertIn("[dry-run] would clear", output)
        self.assertIn("[dry-run] qsub", output)

    def test_clear_markers_dry_run_preserves_existing_marker(self) -> None:
        result, output = self.run_main("--clear-markers", "--dry-run")

        self.assertEqual(result, 0)
        self.assert_marker_unchanged()
        self.assertIn("Would clear 1 marker(s)", output)

    def test_clear_markers_without_dry_run_still_removes_marker(self) -> None:
        result, output = self.run_main("--clear-markers")

        self.assertEqual(result, 0)
        self.assertFalse(self.marker.exists())
        self.assertIn("Cleared 1 marker(s)", output)


if __name__ == "__main__":
    unittest.main()
