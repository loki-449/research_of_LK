#!/usr/bin/env python3
"""验证 VASP 批处理仅在全部体系成功时返回零退出码。

基本用法:
  python -m unittest vasp/tests/test_batch_exit_status.py

参数说明:
  无。测试使用临时路径与 mock，不读写真实计算目录。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_ROOT = Path(__file__).resolve().parents[1] / "scripts"
for subdir in ("lib", "opt", "scf_ELF"):
    sys.path.insert(0, str(SCRIPTS_ROOT / subdir))

import make_poscar
import make_potcar
import run_opt_batch
import run_scf_batch
import scf_contcar_to_poscar_ELF
import setup_opt_workflow


class BatchExitStatusTests(unittest.TestCase):
    """覆盖所有 VASP 批量入口的部分失败退出状态。"""

    def test_run_opt_batch_partial_failure_is_nonzero(self) -> None:
        systems = [Path("/qe/ok"), Path("/qe/bad")]
        with (
            patch.object(run_opt_batch, "find_qe_system_dirs", return_value=systems),
            patch.object(run_opt_batch, "work_root_from_args", return_value=Path("/work")),
            patch.object(run_opt_batch, "process_one", side_effect=[True, False]),
        ):
            self.assertEqual(run_opt_batch.main(["/qe", "--dry-run"]), 1)

    def test_run_scf_batch_partial_failure_is_nonzero(self) -> None:
        systems = [Path("/qe/ok"), Path("/qe/bad")]
        with (
            patch.object(run_scf_batch, "find_qe_system_dirs", return_value=systems),
            patch.object(run_scf_batch, "work_root_from_args", return_value=Path("/work")),
            patch.object(run_scf_batch, "process_one", side_effect=[True, False]),
        ):
            self.assertEqual(run_scf_batch.main(["/qe", "--dry-run"]), 1)

    def test_make_poscar_partial_failure_is_nonzero(self) -> None:
        systems = [Path("/qe/ok"), Path("/qe/bad")]
        with (
            patch.object(make_poscar, "find_qe_system_dirs", return_value=systems),
            patch.object(
                make_poscar,
                "process_qe_system",
                side_effect=[True, False],
            ),
        ):
            self.assertEqual(
                make_poscar.batch_scan(Path("/qe"), Path("/work"), "*GPa*"),
                1,
            )

    def test_make_potcar_partial_failure_is_nonzero(self) -> None:
        poscars = [
            Path("/work/A/1/opt/POSCAR"),
            Path("/work/B/2/opt/POSCAR"),
        ]
        with (
            patch.object(make_potcar, "iter_opt_input_files", return_value=poscars),
            patch.object(make_potcar, "read_poscar_elements", return_value=["H"]),
            patch.object(
                make_potcar,
                "make_for_base",
                side_effect=[None, OSError("write failed")],
            ),
        ):
            self.assertEqual(
                make_potcar.batch_scan(Path("/work"), "/pbe", False),
                1,
            )

    def test_setup_workflow_partial_failure_is_nonzero(self) -> None:
        systems = [Path("/qe/ok"), Path("/qe/bad")]
        with (
            patch.object(
                setup_opt_workflow,
                "find_qe_system_dirs",
                return_value=systems,
            ),
            patch.object(
                setup_opt_workflow,
                "work_root_from_args",
                return_value=Path("/work"),
            ),
            patch.object(
                setup_opt_workflow,
                "setup_one_system",
                side_effect=[True, False],
            ),
        ):
            self.assertEqual(setup_opt_workflow.main(["/qe", "--dry-run"]), 1)

    def test_contcar_copy_partial_failure_is_nonzero(self) -> None:
        contcars = [
            Path("/work/A/1/opt/CONTCAR"),
            Path("/work/B/2/opt/CONTCAR"),
        ]
        with (
            patch.object(
                scf_contcar_to_poscar_ELF,
                "iter_opt_input_files",
                return_value=contcars,
            ),
            patch.object(
                scf_contcar_to_poscar_ELF,
                "copy_contcar_to_poscar",
                side_effect=[True, False],
            ),
        ):
            self.assertEqual(
                scf_contcar_to_poscar_ELF.batch_scan(Path("/work")),
                1,
            )

    def test_all_successful_systems_still_return_zero(self) -> None:
        systems = [Path("/qe/a"), Path("/qe/b")]
        with (
            patch.object(run_opt_batch, "find_qe_system_dirs", return_value=systems),
            patch.object(run_opt_batch, "work_root_from_args", return_value=Path("/work")),
            patch.object(run_opt_batch, "process_one", return_value=True),
        ):
            self.assertEqual(run_opt_batch.main(["/qe", "--dry-run"]), 0)


if __name__ == "__main__":
    unittest.main()
