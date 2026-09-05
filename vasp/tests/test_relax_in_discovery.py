#!/usr/bin/env python3
"""
test_relax_in_discovery.py — QE relax.in 定位回归测试

用途:
  验证 VASP 批量部署不会在多个嵌套 relax.in 之间静默任选一个。

基本用法:
  python -m unittest discover -s vasp/tests -p "test_*.py"

参数说明:
  无命令行参数；仅依赖 Python 标准库。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = REPO_ROOT / "vasp" / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import find_relax_in


class RelaxInDiscoveryTests(unittest.TestCase):
    def test_returns_only_nested_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system_dir = Path(tmp) / "Ag-H-50GPa-300K"
            candidate = system_dir / "run" / "relax.in"
            candidate.parent.mkdir(parents=True)
            candidate.write_text("single", encoding="utf-8")

            self.assertEqual(find_relax_in(system_dir), candidate)

    def test_direct_candidate_keeps_documented_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system_dir = Path(tmp) / "Ag-H-50GPa-300K"
            direct = system_dir / "relax.in"
            nested = system_dir / "run" / "relax.in"
            nested.parent.mkdir(parents=True)
            direct.write_text("direct", encoding="utf-8")
            nested.write_text("nested", encoding="utf-8")

            self.assertEqual(find_relax_in(system_dir), direct)

    def test_rejects_multiple_nested_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system_dir = Path(tmp) / "Ag-H-50GPa-300K"
            first = system_dir / "old_run" / "relax.in"
            second = system_dir / "new_run" / "relax.in"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_text("old", encoding="utf-8")
            second.write_text("new", encoding="utf-8")

            with self.assertRaises(ValueError) as raised:
                find_relax_in(system_dir)
            message = str(raised.exception)
            self.assertIn("old_run/relax.in", message)
            self.assertIn("new_run/relax.in", message)

    def test_batch_entries_fail_without_writing_ambiguous_system(self) -> None:
        scripts = (
            REPO_ROOT / "vasp" / "scripts" / "opt" / "run_opt_batch.py",
            REPO_ROOT / "vasp" / "scripts" / "scf_ELF" / "run_scf_batch.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qe_root = root / "qe"
            system_dir = qe_root / "Ag-H-50GPa-300K"
            for run_name in ("old_run", "new_run"):
                candidate = system_dir / run_name / "relax.in"
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.write_text(run_name, encoding="utf-8")

            work_root = root / "work"
            for script in scripts:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        str(qe_root),
                        "--work-root",
                        str(work_root),
                        "--dry-run",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("Multiple relax.in files found", result.stdout)
                self.assertFalse(work_root.exists())


if __name__ == "__main__":
    unittest.main()
