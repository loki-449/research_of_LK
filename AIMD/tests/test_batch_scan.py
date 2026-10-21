#!/usr/bin/env python3
"""
测试 AIMD 批量扫描对缺失 XDATCAR 的完整性校验。

基本用法:
  python3 -m unittest AIMD.tests.test_batch_scan

参数说明:
  无命令行参数；测试在临时工作根中构造有效与缺失的轨迹体系。
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

AIMD_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AIMD_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(AIMD_ROOT / "scripts" / "MSD_RMSD"))

from extract_msd_flex import main as extract_main
from msd_common import find_missing_aimd_xdatcars
from run_msd_batch import main as batch_main


class BatchScanCompletenessTests(unittest.TestCase):
    """验证缺失轨迹不会被批量入口静默忽略。"""

    entrypoints = ((extract_main, ["--scan"]), (batch_main, []))

    def make_work_root(self, base: Path) -> Path:
        """创建一个有效体系和一个缺失 XDATCAR 的体系。"""
        valid_aimd = base / "Valid" / "AIMD"
        valid_aimd.mkdir(parents=True)
        (valid_aimd / "XDATCAR").write_text("placeholder\n", encoding="utf-8")
        (base / "Missing" / "AIMD").mkdir(parents=True)
        return base

    def run_entrypoint(self, entrypoint, extra_args, work_root: Path):
        """以 dry-run 运行一个批量入口并捕获标准输出。"""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = entrypoint(
                extra_args
                + [
                    "--work-root",
                    str(work_root),
                    "--dt",
                    "1.0",
                    "--dry-run",
                ]
            )
        return status, output.getvalue()

    def test_finds_aimd_directory_without_xdatcar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = self.make_work_root(Path(tmp))

            missing = find_missing_aimd_xdatcars(work_root)

            self.assertEqual(
                missing, [work_root / "Missing" / "AIMD" / "XDATCAR"]
            )

    def test_finds_dangling_xdatcar_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            aimd_dir = work_root / "Dangling" / "AIMD"
            aimd_dir.mkdir(parents=True)
            xdatcar = aimd_dir / "XDATCAR"
            xdatcar.symlink_to(work_root / "does-not-exist")

            self.assertEqual(find_missing_aimd_xdatcars(work_root), [xdatcar])

    def test_ignores_system_without_aimd_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            (work_root / "OptOnly" / "opt").mkdir(parents=True)

            self.assertEqual(find_missing_aimd_xdatcars(work_root), [])

    def test_batch_entrypoints_fail_incomplete_scan(self) -> None:
        for entrypoint, extra_args in self.entrypoints:
            with self.subTest(entrypoint=entrypoint.__module__):
                with tempfile.TemporaryDirectory() as tmp:
                    work_root = self.make_work_root(Path(tmp))
                    status, output = self.run_entrypoint(
                        entrypoint, extra_args, work_root
                    )

                    self.assertEqual(status, 1)
                    self.assertIn("missing or invalid XDATCAR", output)
                    self.assertIn("Finished: 1/2", output)

    def test_batch_entrypoints_count_only_missing_system(self) -> None:
        for entrypoint, extra_args in self.entrypoints:
            with self.subTest(entrypoint=entrypoint.__module__):
                with tempfile.TemporaryDirectory() as tmp:
                    work_root = Path(tmp)
                    (work_root / "Missing" / "AIMD").mkdir(parents=True)
                    status, output = self.run_entrypoint(
                        entrypoint, extra_args, work_root
                    )

                    self.assertEqual(status, 1)
                    self.assertIn("Finished: 0/1", output)

    def test_batch_entrypoints_keep_complete_scan_successful(self) -> None:
        for entrypoint, extra_args in self.entrypoints:
            with self.subTest(entrypoint=entrypoint.__module__):
                with tempfile.TemporaryDirectory() as tmp:
                    work_root = Path(tmp)
                    aimd_dir = work_root / "Valid" / "AIMD"
                    aimd_dir.mkdir(parents=True)
                    (aimd_dir / "XDATCAR").write_text(
                        "placeholder\n", encoding="utf-8"
                    )
                    status, output = self.run_entrypoint(
                        entrypoint, extra_args, work_root
                    )

                    self.assertEqual(status, 0)
                    self.assertIn("Finished: 1/1", output)


if __name__ == "__main__":
    unittest.main()
