#!/usr/bin/env python3
"""
test_msd_output_lock.py — 验证 MSD 输出的跨进程互斥保护

用途:
  防止两个提取进程同时写入并发布同一体系的 DAT 文件。

基本用法:
  python -m unittest AIMD/tests/test_msd_output_lock.py

参数说明:
  无命令行参数。
"""
from __future__ import annotations

import io
import multiprocessing
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import numpy as np


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR / "lib"))
sys.path.insert(0, str(SCRIPTS_DIR / "MSD_RMSD"))

import extract_msd_flex
from msd_common import (
    OutputLockedError,
    exclusive_output_lock,
    load_dat,
    published_dat_path,
)


def run_extract_worker(
    work_root: str,
    block_in_reader: bool,
    reader_entered,
    reader_release,
    result_queue,
) -> None:
    """在独立进程运行一次真实写入/发布流程，并暴露读取同步点。"""
    root = Path(work_root)
    xdatcar = root / "sample" / "AIMD" / "XDATCAR"

    def controlled_reader(_path):
        if not block_in_reader:
            raise AssertionError("竞争进程不应进入已加锁的读取阶段")
        reader_entered.set()
        if not reader_release.wait(5):
            raise TimeoutError("等待并发测试释放读取阶段超时")
        positions = np.array(
            [
                [[0.0, 0.0, 0.0]],
                [[0.1, 0.0, 0.0]],
            ]
        )
        return positions, ["H"]

    try:
        with mock.patch.object(
            extract_msd_flex, "read_xdatcar", side_effect=controlled_reader
        ):
            ok = extract_msd_flex.extract_one(
                xdatcar=xdatcar,
                work_root=root,
                dt=1.0,
                output=None,
                stride=1,
                elements=None,
                element_order="file",
                keep_local=False,
                no_publish=False,
                dry_run=False,
            )
        result_queue.put(("ok", ok))
    except BaseException as exc:
        result_queue.put(("error", repr(exc)))


class MsdOutputLockTest(unittest.TestCase):
    """检查锁冲突、释放及提取入口的失败行为。"""

    def test_second_writer_is_rejected_and_lock_is_reusable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.dat"

            with exclusive_output_lock(output):
                with self.assertRaises(OutputLockedError):
                    with exclusive_output_lock(output):
                        self.fail("第二个写入者不应获得同一输出锁")

            with self.assertRaisesRegex(RuntimeError, "测试异常"):
                with exclusive_output_lock(output):
                    raise RuntimeError("测试异常")

            with exclusive_output_lock(output):
                pass

    def test_concurrent_extract_rejects_second_writer_and_publishes_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            system_dir = work_root / "sample"
            aimd_dir = system_dir / "AIMD"
            aimd_dir.mkdir(parents=True)
            xdatcar = aimd_dir / "XDATCAR"
            xdatcar.touch()

            context = multiprocessing.get_context("fork")
            reader_entered = context.Event()
            reader_release = context.Event()
            first_result = context.Queue()
            second_result = context.Queue()
            first = context.Process(
                target=run_extract_worker,
                args=(
                    str(work_root),
                    True,
                    reader_entered,
                    reader_release,
                    first_result,
                ),
            )
            second = context.Process(
                target=run_extract_worker,
                args=(
                    str(work_root),
                    False,
                    reader_entered,
                    reader_release,
                    second_result,
                ),
            )

            first.start()
            try:
                self.assertTrue(
                    reader_entered.wait(5), "首进程未进入受锁保护的读取阶段"
                )
                second.start()
                second.join(5)
                self.assertFalse(second.is_alive(), "竞争进程未快速失败")
                self.assertEqual(second_result.get(timeout=2), ("ok", False))
            finally:
                reader_release.set()
                first.join(5)
                if first.is_alive():
                    first.terminate()
                    first.join()
                if second.is_alive():
                    second.terminate()
                    second.join()

            self.assertEqual(first.exitcode, 0)
            self.assertEqual(second.exitcode, 0)
            self.assertEqual(first_result.get(timeout=2), ("ok", True))

            target = published_dat_path(work_root, system_dir.name)
            self.assertTrue(target.is_file())
            self.assertFalse((system_dir / "msd_data.dat").exists())
            data = load_dat(target)
            self.assertEqual(len(data["Time(ps)"]), 2)
            self.assertAlmostEqual(data["H_MSD(A2)"][1], 0.01)

    def test_locked_cli_returns_nonzero_with_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            xdatcar = work_root / "sample" / "AIMD" / "XDATCAR"
            xdatcar.parent.mkdir(parents=True)
            xdatcar.touch()

            target = published_dat_path(work_root, "sample")
            output = io.StringIO()
            with exclusive_output_lock(target), redirect_stdout(output):
                exit_code = extract_msd_flex.main(
                    [
                        str(xdatcar),
                        "--work-root",
                        str(work_root),
                        "--dt",
                        "1.0",
                        "--stride",
                        "1",
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("already being generated by another process", output.getvalue())


if __name__ == "__main__":
    unittest.main()
