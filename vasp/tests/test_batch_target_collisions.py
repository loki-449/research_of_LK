#!/usr/bin/env python3
"""
test_batch_target_collisions.py — VASP 批量目标目录冲突回归测试

用途:
  验证多个 QE 体系映射到同一 <材料>/<压强> 目录时，所有批量部署入口
  都会在写入前失败，避免后处理输入静默覆盖先处理输入。

基本用法:
  python -m unittest vasp/tests/test_batch_target_collisions.py

参数说明:
  无命令行参数；测试使用临时 QE 与工作目录。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VASP_SCRIPTS = REPO_ROOT / "vasp" / "scripts"
sys.path.insert(0, str(VASP_SCRIPTS / "lib"))

from vasp_common import validate_unique_system_targets


def load_entrypoint(relative_path: str, module_name: str):
    """按文件路径加载入口脚本，避免要求 scripts 目录成为 Python 包。"""
    path = VASP_SCRIPTS / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load test module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BatchTargetCollisionTests(unittest.TestCase):
    """批量入口必须拒绝会覆盖同一目标目录的输入集合。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.entrypoints = {
            "run_opt_batch": (
                load_entrypoint("opt/run_opt_batch.py", "test_run_opt_batch"),
                lambda qe, work: [str(qe), "--work-root", str(work)],
            ),
            "setup_opt_workflow": (
                load_entrypoint(
                    "opt/setup_opt_workflow.py", "test_setup_opt_workflow"
                ),
                lambda qe, work: [str(qe), "--work-root", str(work)],
            ),
            "make_poscar": (
                load_entrypoint("opt/make_poscar.py", "test_make_poscar"),
                lambda qe, work: [
                    "--scan",
                    str(qe),
                    "--work-root",
                    str(work),
                ],
            ),
            "run_scf_batch": (
                load_entrypoint("scf_ELF/run_scf_batch.py", "test_run_scf_batch"),
                lambda qe, work: [str(qe), "--work-root", str(work)],
            ),
        }

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.qe_root = self.root / "qe"
        self.qe_root.mkdir()
        self.systems = [
            self.qe_root / "Ag-H-50GPa-300K",
            self.qe_root / "Ag-H-50GPa-600K",
        ]
        for system in self.systems:
            system.mkdir()

    def test_validator_reports_all_colliding_inputs(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"Ag/50.*Ag-H-50GPa-300K.*Ag-H-50GPa-600K",
        ):
            validate_unique_system_targets(self.systems)

    def test_batch_entrypoints_fail_before_creating_outputs(self) -> None:
        for name, (module, build_argv) in self.entrypoints.items():
            with self.subTest(entrypoint=name):
                work_root = self.root / f"work-{name}"
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = module.main(build_argv(self.qe_root, work_root))

                self.assertEqual(result, 1)
                self.assertIn("same VASP target directory", stdout.getvalue())
                self.assertFalse(work_root.exists())

    def test_distinct_targets_are_accepted(self) -> None:
        other = self.qe_root / "Ag-H-80GPa-600K"
        other.mkdir()
        validate_unique_system_targets([self.systems[0], other])


if __name__ == "__main__":
    unittest.main()
