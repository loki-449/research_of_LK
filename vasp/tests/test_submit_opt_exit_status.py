#!/usr/bin/env python3
"""
test_submit_opt_exit_status.py — PBS 批量提交退出状态回归测试

用途:
  验证部分 qsub 失败或队列限额中止时，submit_opt 不会返回成功。

基本用法:
  python -m unittest vasp/tests/test_submit_opt_exit_status.py

参数说明:
  无命令行参数；测试使用临时目录和模拟 PBS 命令，不会提交真实作业。
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


OPT_SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "opt"
sys.path.insert(0, str(OPT_SCRIPT_DIR))

import submit_opt


class SubmitOptExitStatusTests(unittest.TestCase):
    def make_opt_dir(self, root: Path, material: str) -> Path:
        """创建具备完整核心输入的最小 opt 目录。"""
        opt_dir = root / material / "50" / "opt"
        opt_dir.mkdir(parents=True)
        (opt_dir / "opt.pbs").write_text("#!/bin/bash\n", encoding="utf-8")
        (opt_dir / "POSCAR").write_text("structure\n", encoding="utf-8")
        (opt_dir / "POTCAR").write_text("potential\n", encoding="utf-8")
        return opt_dir

    def submit(self, work_root: Path) -> tuple[int, str]:
        """按非 dry-run 模式调用批量提交并捕获输出。"""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = submit_opt.submit_all(
                work_root,
                max_jobs=8,
                wait_interval=1,
                no_wait=True,
                resubmit=False,
                clear_only=False,
                dry_run=False,
            )
        return status, output.getvalue()

    def test_partial_qsub_failure_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            failed_dir = self.make_opt_dir(root, "Ag")
            submitted_dir = self.make_opt_dir(root, "La")

            with (
                mock.patch.object(submit_opt, "wait_for_slot", return_value=0),
                mock.patch.object(submit_opt, "chmod_executable"),
                mock.patch.object(
                    submit_opt,
                    "qsub_job",
                    side_effect=[RuntimeError("scheduler rejected job"), "2.server"],
                ),
            ):
                status, output = self.submit(root)

            self.assertEqual(status, 1)
            self.assertIn("failed=1", output)
            self.assertFalse((failed_dir / submit_opt.MARKER_NAME).exists())
            self.assertTrue((submitted_dir / submit_opt.MARKER_NAME).is_file())

    def test_queue_limit_stop_after_submission_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            submitted_dir = self.make_opt_dir(root, "Ag")
            pending_dir = self.make_opt_dir(root, "La")

            with (
                mock.patch.object(
                    submit_opt, "wait_for_slot", side_effect=[0, None]
                ),
                mock.patch.object(
                    submit_opt, "jobs_within_limit", return_value=(False, 9)
                ),
                mock.patch.object(submit_opt, "chmod_executable"),
                mock.patch.object(
                    submit_opt, "qsub_job", return_value="1.server"
                ),
            ):
                status, output = self.submit(root)

            self.assertEqual(status, 1)
            self.assertIn("stopped_at_limit=1", output)
            self.assertTrue((submitted_dir / submit_opt.MARKER_NAME).is_file())
            self.assertFalse((pending_dir / submit_opt.MARKER_NAME).exists())


if __name__ == "__main__":
    unittest.main()
