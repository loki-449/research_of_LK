#!/usr/bin/env python3
"""
test_submit_opt_qstat_failure.py — PBS 队列查询失败回归测试

用途:
  验证无法取得可靠 qstat 结果时停止提交，避免绕过批量作业上限。

基本用法:
  python -m unittest vasp/tests/test_submit_opt_qstat_failure.py

参数说明:
  无命令行参数；测试使用临时目录和模拟 PBS 命令，不会提交真实作业。
"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


OPT_SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "opt"
sys.path.insert(0, str(OPT_SCRIPT_DIR))

import submit_opt


class SubmitOptQstatFailureTests(unittest.TestCase):
    def make_opt_dir(self, root: Path) -> Path:
        """创建带 PBS 脚本的最小 opt 目录。"""
        opt_dir = root / "Ag" / "50" / "opt"
        opt_dir.mkdir(parents=True)
        (opt_dir / submit_opt.OPT_PBS_SCRIPT).write_text(
            "#!/bin/bash\n", encoding="utf-8"
        )
        return opt_dir

    def submit(self, work_root: Path) -> tuple[int, str]:
        """执行非 dry-run 批量提交并捕获标准输出。"""
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

    def test_qstat_nonzero_aborts_before_qsub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            opt_dir = self.make_opt_dir(root)
            failed_qstat = subprocess.CompletedProcess(
                ["qstat", "-u", "researcher"],
                returncode=153,
                stdout="",
                stderr="cannot connect to server",
            )

            with (
                mock.patch.dict(os.environ, {"USER": "researcher"}, clear=False),
                mock.patch.object(
                    submit_opt.subprocess, "run", return_value=failed_qstat
                ),
                mock.patch.object(submit_opt, "qsub_job") as qsub_job,
            ):
                status, output = self.submit(root)

            self.assertEqual(status, 1)
            self.assertIn("cannot verify PBS job count", output)
            self.assertIn("cannot connect to server", output)
            qsub_job.assert_not_called()
            self.assertFalse((opt_dir / submit_opt.MARKER_NAME).exists())

    def test_missing_user_aborts_before_qsub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_opt_dir(root)

            with (
                mock.patch.dict(os.environ, {}, clear=True),
                mock.patch.object(submit_opt, "qsub_job") as qsub_job,
            ):
                status, output = self.submit(root)

            self.assertEqual(status, 1)
            self.assertIn("USER/USERNAME is not set", output)
            qsub_job.assert_not_called()


if __name__ == "__main__":
    unittest.main()
