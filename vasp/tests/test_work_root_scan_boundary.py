#!/usr/bin/env python3
"""
test_work_root_scan_boundary.py — VASP 工作根扫描边界回归测试。

用途:
  验证 opt 批量扫描不会跟随工作根内的符号链接访问根外计算目录，
  从而避免覆盖根外输入、写提交标记或提交非目标作业。

基本用法:
  python3 -m unittest vasp/tests/test_work_root_scan_boundary.py -v

参数说明:
  无。测试仅使用 Python 标准库与临时目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
OPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "opt"
SCF_DIR = Path(__file__).resolve().parents[1] / "scripts" / "scf_ELF"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(OPT_DIR))
sys.path.insert(0, str(SCF_DIR))

from vasp_common import iter_opt_input_files, iter_opt_work_dirs  # noqa: E402
from make_potcar import batch_scan as make_potcar_batch_scan  # noqa: E402
from scf_contcar_to_poscar_ELF import batch_scan as scf_batch_scan  # noqa: E402
import submit_opt  # noqa: E402
from submit_opt import find_opt_dirs  # noqa: E402


class WorkRootScanBoundaryTests(unittest.TestCase):
    """验证 opt 目录与输入文件扫描均限制在工作根内。"""

    def make_symlink(
        self,
        link: Path,
        target: Path,
        target_is_directory: bool = False,
    ) -> None:
        """建立测试链接；文件系统不支持时跳过当前用例。"""
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as exc:
            self.skipTest(f"当前文件系统不支持符号链接: {exc}")

    def test_normal_opt_tree_is_discovered(self) -> None:
        """普通工作根内目录仍应被两个扫描器发现。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "calc"
            opt_dir = root / "Ag" / "50" / "opt"
            opt_dir.mkdir(parents=True)
            poscar = opt_dir / "POSCAR"
            poscar.write_text("test\n", encoding="utf-8")

            self.assertEqual(iter_opt_work_dirs(root), [opt_dir])
            self.assertEqual(iter_opt_input_files(root, "POSCAR"), [poscar])

    def test_external_material_symlink_is_rejected(self) -> None:
        """指向根外材料树的链接不得进入目录或文件扫描结果。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            outside_opt = parent / "outside" / "50" / "opt"
            outside_opt.mkdir(parents=True)
            (outside_opt / "POSCAR").write_text("outside\n", encoding="utf-8")
            root.mkdir()

            link = root / "Ag"
            self.make_symlink(
                link,
                outside_opt.parent.parent,
                target_is_directory=True,
            )

            self.assertEqual(iter_opt_work_dirs(root), [])
            self.assertEqual(iter_opt_input_files(root, "POSCAR"), [])

    def test_make_potcar_rejects_external_final_output_symlink(self) -> None:
        """批量 POTCAR 不得通过正式输出链接覆盖根外文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            opt_dir = root / "H" / "50" / "opt"
            opt_dir.mkdir(parents=True)
            (opt_dir / "POSCAR").write_text(
                "H\n1.0\n1 0 0\n0 1 0\n0 0 1\nH\n1\nDirect\n0 0 0\n",
                encoding="utf-8",
            )
            outside = parent / "outside.POTCAR"
            outside.write_text("keep\n", encoding="utf-8")
            self.make_symlink(opt_dir / "POTCAR", outside)

            pbe = parent / "pbe" / "H"
            pbe.mkdir(parents=True)
            (pbe / "POTCAR").write_text(
                "PAW_PBE H 01Jan2020\nZVAL = 1.0\n",
                encoding="utf-8",
            )

            result = make_potcar_batch_scan(root, pbe.parent, keep_single=False)

            self.assertEqual(result, 1)
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")

    def test_make_potcar_rejects_external_temporary_output_symlink(self) -> None:
        """批量 POTCAR 不得通过单元素临时文件链接覆盖根外文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            opt_dir = root / "H" / "50" / "opt"
            opt_dir.mkdir(parents=True)
            (opt_dir / "POSCAR").write_text(
                "H\n1.0\n1 0 0\n0 1 0\n0 0 1\nH\n1\nDirect\n0 0 0\n",
                encoding="utf-8",
            )
            outside = parent / "outside-single.POTCAR"
            outside.write_text("keep\n", encoding="utf-8")
            self.make_symlink(opt_dir / "H.POTCAR", outside)

            pbe = parent / "pbe" / "H"
            pbe.mkdir(parents=True)
            (pbe / "POTCAR").write_text(
                "PAW_PBE H 01Jan2020\nZVAL = 1.0\n",
                encoding="utf-8",
            )

            result = make_potcar_batch_scan(root, pbe.parent, keep_single=False)

            self.assertEqual(result, 1)
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")

    def test_scf_copy_rejects_external_stage_directory_symlink(self) -> None:
        """CONTCAR 批量复制不得写入根外 scf_ELF 目录。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            base = root / "Ag" / "50"
            opt_dir = base / "opt"
            opt_dir.mkdir(parents=True)
            (opt_dir / "CONTCAR").write_text("new structure\n", encoding="utf-8")

            outside = parent / "outside-scf"
            outside.mkdir()
            outside_poscar = outside / "POSCAR"
            outside_poscar.write_text("keep\n", encoding="utf-8")
            self.make_symlink(base / "scf_ELF", outside, target_is_directory=True)

            result = scf_batch_scan(root)

            self.assertEqual(result, 1)
            self.assertEqual(outside_poscar.read_text(encoding="utf-8"), "keep\n")

    def test_scf_copy_rejects_external_pbs_symlink(self) -> None:
        """请求写 PBS 时不得通过 ELF.pbs 链接覆盖根外脚本。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            base = root / "Ag" / "50"
            opt_dir = base / "opt"
            scf_dir = base / "scf_ELF"
            opt_dir.mkdir(parents=True)
            scf_dir.mkdir()
            (opt_dir / "CONTCAR").write_text("new structure\n", encoding="utf-8")

            outside = parent / "outside.pbs"
            outside.write_text("keep\n", encoding="utf-8")
            self.make_symlink(scf_dir / "ELF.pbs", outside)

            result = scf_batch_scan(root, write_pbs=True)

            self.assertEqual(result, 1)
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse((scf_dir / "POSCAR").exists())

    def test_submit_rejects_external_pbs_symlink(self) -> None:
        """提交扫描不得 chmod 或提交根外 opt.pbs。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            opt_dir = root / "Ag" / "50" / "opt"
            opt_dir.mkdir(parents=True)
            outside = parent / "outside.pbs"
            outside.write_text("#!/bin/bash\n", encoding="utf-8")
            self.make_symlink(opt_dir / "opt.pbs", outside)

            self.assertEqual(find_opt_dirs(root), [])

    def test_submit_rejects_external_marker_symlink(self) -> None:
        """提交扫描不得通过 marker 链接覆盖根外文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            opt_dir = root / "Ag" / "50" / "opt"
            opt_dir.mkdir(parents=True)
            (opt_dir / "opt.pbs").write_text("#!/bin/bash\n", encoding="utf-8")
            outside = parent / "outside.marker"
            outside.write_text("keep\n", encoding="utf-8")
            self.make_symlink(opt_dir / ".pbs_submitted", outside)

            self.assertEqual(find_opt_dirs(root), [])
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")

    def test_submit_rechecks_paths_after_queue_wait(self) -> None:
        """队列等待期间替换链接后不得 chmod 或提交根外脚本。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            opt_dir = root / "Ag" / "50" / "opt"
            opt_dir.mkdir(parents=True)
            script = opt_dir / "opt.pbs"
            script.write_text("#!/bin/bash\n", encoding="utf-8")
            outside_script = parent / "outside.pbs"
            outside_script.write_text("#!/bin/bash\n", encoding="utf-8")
            outside_marker = parent / "outside.marker"
            outside_marker.write_text("keep\n", encoding="utf-8")

            def replace_paths(*_args, **_kwargs):
                script.unlink()
                self.make_symlink(script, outside_script)
                self.make_symlink(opt_dir / ".pbs_submitted", outside_marker)
                return 0

            with mock.patch.object(
                submit_opt,
                "wait_for_slot",
                side_effect=replace_paths,
            ), mock.patch.object(
                submit_opt,
                "qsub_job",
                side_effect=AssertionError("不应提交根外脚本"),
            ):
                result = submit_opt.submit_all(
                    root,
                    max_jobs=8,
                    wait_interval=60,
                    no_wait=False,
                    resubmit=False,
                    clear_only=False,
                    dry_run=False,
                )

            self.assertEqual(result, 1)
            self.assertEqual(outside_marker.read_text(encoding="utf-8"), "keep\n")

    def test_submit_rechecks_marker_after_qsub(self) -> None:
        """qsub 返回后新出现的根外 marker 链接不得被写入。"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "calc"
            opt_dir = root / "Ag" / "50" / "opt"
            opt_dir.mkdir(parents=True)
            (opt_dir / "opt.pbs").write_text("#!/bin/bash\n", encoding="utf-8")
            outside_marker = parent / "outside.marker"
            outside_marker.write_text("keep\n", encoding="utf-8")

            def qsub_then_replace_marker(*_args, **_kwargs):
                self.make_symlink(opt_dir / ".pbs_submitted", outside_marker)
                return "123.server"

            with mock.patch.object(
                submit_opt,
                "wait_for_slot",
                return_value=0,
            ), mock.patch.object(
                submit_opt,
                "qsub_job",
                side_effect=qsub_then_replace_marker,
            ):
                result = submit_opt.submit_all(
                    root,
                    max_jobs=8,
                    wait_interval=60,
                    no_wait=False,
                    resubmit=False,
                    clear_only=False,
                    dry_run=False,
                )

            self.assertEqual(result, 1)
            self.assertEqual(outside_marker.read_text(encoding="utf-8"), "keep\n")


if __name__ == "__main__":
    unittest.main()
