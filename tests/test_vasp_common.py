#!/usr/bin/env python3
"""
测试 VASP 公共脚本模板的关键安全行为。

基本用法:
  python -m unittest tests.test_vasp_common

参数说明:
  无命令行参数；测试使用临时目录模拟 PBS 作业启动环境。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "vasp" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import PBS_HEADER


def pbs_cd_command() -> str:
    """返回 PBS 模板中切换工作目录的命令。"""
    return next(line for line in PBS_HEADER.splitlines() if line.startswith("cd "))


class PbsHeaderTests(unittest.TestCase):
    """验证 PBS 作业只在预期工作目录内继续执行。"""

    def test_work_directory_with_spaces(self) -> None:
        """含空格的 PBS 工作目录应能被完整识别。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            launch_dir = root / "launch"
            work_dir = root / "work dir"
            launch_dir.mkdir()
            work_dir.mkdir()
            env = os.environ.copy()
            env["PBS_O_WORKDIR"] = str(work_dir)

            result = subprocess.run(
                ["bash", "-c", f"{pbs_cd_command()}\nprintf '%s' \"$PWD\""],
                cwd=launch_dir,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, str(work_dir))

    def test_missing_work_directory_stops_job(self) -> None:
        """工作目录不可达时不得继续生成计算文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            launch_dir = root / "launch"
            launch_dir.mkdir()
            marker = launch_dir / "continued"
            env = os.environ.copy()
            env["PBS_O_WORKDIR"] = str(root / "missing")

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f"{pbs_cd_command()}\nprintf reached > {marker}",
                ],
                cwd=launch_dir,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
