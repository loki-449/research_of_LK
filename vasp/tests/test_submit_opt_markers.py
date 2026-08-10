#!/usr/bin/env python3
"""
test_submit_opt_markers.py — PBS 提交标记并发安全回归测试。

用途:
  验证同一 opt 目录在 qsub 前被排他预留，避免并发入口重复提交；
  验证 qsub 失败会回滚预留，而提交成功后的标记更新失败会保留预留。

基本用法:
  python3 -m unittest vasp/tests/test_submit_opt_markers.py -v

参数说明:
  无。测试仅使用临时目录和 mock，不调用真实 PBS 命令。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_ROOT = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT / "lib"))
sys.path.insert(0, str(SCRIPTS_ROOT / "opt"))

import submit_opt  # noqa: E402


class SubmissionMarkerTests(unittest.TestCase):
    """验证提交标记在外部 qsub 副作用前提供排他保护。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.work_root = Path(self.temp_dir.name)
        self.opt_dir = self.work_root / "H" / "100" / "opt"
        self.opt_dir.mkdir(parents=True)
        (self.opt_dir / "opt.pbs").write_text("#!/bin/bash\n", encoding="utf-8")
        (self.opt_dir / "POSCAR").write_text("valid input\n", encoding="utf-8")
        (self.opt_dir / "POTCAR").write_bytes(b"valid pseudopotential\n")

    def run_submit(self) -> int:
        """在 mock 队列计数下提交单个临时体系。"""
        with (
            patch.object(submit_opt, "wait_for_slot", return_value=0),
            patch.object(submit_opt, "chmod_executable"),
        ):
            return submit_opt.submit_all(
                self.work_root,
                max_jobs=8,
                wait_interval=0,
                no_wait=True,
                resubmit=False,
                clear_only=False,
                dry_run=False,
            )

    def test_reservation_creation_is_exclusive(self) -> None:
        """第二个并发入口不能取得同一目录的提交预留。"""
        submit_opt.reserve_submission(self.opt_dir)

        with self.assertRaises(FileExistsError):
            submit_opt.reserve_submission(self.opt_dir)

        marker = submit_opt.marker_path(self.opt_dir).read_text(encoding="utf-8")
        self.assertIn("status=submitting", marker)

    def test_qsub_failure_removes_reservation(self) -> None:
        """外部提交失败后允许后续调用正常重试。"""
        with patch.object(
            submit_opt,
            "qsub_job",
            side_effect=RuntimeError("scheduler rejected job"),
        ):
            self.assertEqual(self.run_submit(), 1)

        self.assertFalse(submit_opt.marker_path(self.opt_dir).exists())

    def test_marker_update_failure_keeps_reservation(self) -> None:
        """qsub 已成功时，即使 job ID 写回失败也不能重新开放提交。"""
        with (
            patch.object(submit_opt, "qsub_job", return_value="123.server"),
            patch.object(
                submit_opt,
                "write_marker",
                side_effect=OSError("disk full"),
            ),
        ):
            self.assertEqual(self.run_submit(), 0)

        marker = submit_opt.marker_path(self.opt_dir).read_text(encoding="utf-8")
        self.assertIn("status=submitting", marker)

        with patch.object(submit_opt, "qsub_job") as qsub:
            self.assertEqual(self.run_submit(), 0)
            qsub.assert_not_called()


if __name__ == "__main__":
    unittest.main()
