#!/usr/bin/env python3
"""
验证 MSD 绘图不会把一个体系的数据发布为另一个体系的结果。

基本用法:
  python3 -m unittest AIMD/tests/test_plot_msd_flex_identity.py

参数说明:
  无命令行参数；测试在临时目录中构造标准汇总 dat 路径。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = REPO_ROOT / "AIMD" / "scripts" / "lib"
PLOT_SCRIPT = (
    REPO_ROOT / "AIMD" / "scripts" / "MSD_RMSD" / "plot_msd_flex.py"
)
sys.path.insert(0, str(LIB_DIR))

from msd_common import system_from_canonical_dat_path


class PlotMsdIdentityTests(unittest.TestCase):
    def run_plot(
        self, datafile: Path, work_root: Path, system_dir: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(PLOT_SCRIPT),
                str(datafile),
                "--work-root",
                str(work_root),
                "--system-dir",
                str(system_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_infers_system_only_from_canonical_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)

            archive = work_root / "MSD_data_for_origin" / "Ba3_msd_data.dat"
            local = work_root / "Ag5" / "msd_data.dat"
            custom = work_root / "custom" / "result.dat"

            self.assertEqual(
                system_from_canonical_dat_path(archive, work_root), "Ba3"
            )
            self.assertEqual(
                system_from_canonical_dat_path(local, work_root), "Ag5"
            )
            self.assertIsNone(
                system_from_canonical_dat_path(custom, work_root)
            )

    def test_rejects_mismatched_datafile_before_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            archive = work_root / "MSD_data_for_origin"
            archive.mkdir()
            datafile = archive / "Ba3_msd_data.dat"
            datafile.write_text("# placeholder\n", encoding="utf-8")

            wrong_system_dir = work_root / "Ag5"
            wrong_system_dir.mkdir()

            result = self.run_plot(datafile, work_root, wrong_system_dir)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("datafile belongs to system 'Ba3'", result.stdout)
            self.assertFalse(
                (work_root / "MSD_png" / "Ag5_msd_rmsd.png").exists()
            )

    def test_rejects_mismatched_symlink_at_canonical_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            target = work_root / "source.dat"
            target.write_text("# placeholder\n", encoding="utf-8")

            archive = work_root / "MSD_data_for_origin"
            archive.mkdir()
            archive_link = archive / "Ba3_msd_data.dat"
            archive_link.symlink_to(target)

            local_dir = work_root / "Ba3"
            local_dir.mkdir()
            local_link = local_dir / "msd_data.dat"
            local_link.symlink_to(target)

            wrong_system_dir = work_root / "Ag5"
            wrong_system_dir.mkdir()

            for datafile in (archive_link, local_link):
                with self.subTest(datafile=datafile):
                    result = self.run_plot(
                        datafile, work_root, wrong_system_dir
                    )
                    self.assertEqual(
                        result.returncode, 1, result.stdout + result.stderr
                    )
                    self.assertIn(
                        "datafile belongs to system 'Ba3'", result.stdout
                    )
                    self.assertFalse(
                        (
                            work_root
                            / "MSD_png"
                            / "Ag5_msd_rmsd.png"
                        ).exists()
                    )

    def test_rejects_mismatch_through_symlinked_work_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            work_root = base / "real_work"
            work_root.mkdir()
            linked_root = base / "linked_work"
            linked_root.symlink_to(work_root, target_is_directory=True)

            archive = work_root / "MSD_data_for_origin"
            archive.mkdir()
            archive_data = archive / "Ba3_msd_data.dat"
            archive_data.write_text("# placeholder\n", encoding="utf-8")

            local_dir = work_root / "Ba3"
            local_dir.mkdir()
            local_data = local_dir / "msd_data.dat"
            local_data.write_text("# placeholder\n", encoding="utf-8")

            wrong_system_dir = linked_root / "Ag5"
            wrong_system_dir.mkdir()

            linked_inputs = (
                linked_root / "MSD_data_for_origin" / archive_data.name,
                linked_root / "Ba3" / local_data.name,
            )
            for datafile in linked_inputs:
                with self.subTest(datafile=datafile):
                    result = self.run_plot(
                        datafile, linked_root, wrong_system_dir
                    )
                    self.assertEqual(
                        result.returncode, 1, result.stdout + result.stderr
                    )
                    self.assertIn(
                        "datafile belongs to system 'Ba3'", result.stdout
                    )
                    self.assertFalse(
                        (
                            work_root
                            / "MSD_png"
                            / "Ag5_msd_rmsd.png"
                        ).exists()
                    )

    def test_rejects_mismatch_through_symlinked_layout_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            work_root = base / "work"
            work_root.mkdir()

            archive_target = base / "archive_target"
            archive_target.mkdir()
            archive_data = archive_target / "Ba3_msd_data.dat"
            archive_data.write_text("# placeholder\n", encoding="utf-8")
            (work_root / "MSD_data_for_origin").symlink_to(
                archive_target, target_is_directory=True
            )

            local_target = base / "local_target"
            local_target.mkdir()
            local_data = local_target / "msd_data.dat"
            local_data.write_text("# placeholder\n", encoding="utf-8")
            (work_root / "Ba3").symlink_to(
                local_target, target_is_directory=True
            )

            wrong_system_dir = work_root / "Ag5"
            wrong_system_dir.mkdir()

            linked_inputs = (
                work_root / "MSD_data_for_origin" / archive_data.name,
                work_root / "Ba3" / local_data.name,
            )
            for datafile in linked_inputs:
                with self.subTest(datafile=datafile):
                    result = self.run_plot(
                        datafile, work_root, wrong_system_dir
                    )
                    self.assertEqual(
                        result.returncode, 1, result.stdout + result.stderr
                    )
                    self.assertIn(
                        "datafile belongs to system 'Ba3'", result.stdout
                    )
                    self.assertFalse(
                        (
                            work_root
                            / "MSD_png"
                            / "Ag5_msd_rmsd.png"
                        ).exists()
                    )

    def test_allows_custom_datafile_with_explicit_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            custom_dir = work_root / "custom"
            custom_dir.mkdir()
            datafile = custom_dir / "result.dat"
            datafile.write_text(
                "# Time(ps) H_MSD(A2) H_RMSD(A)\n"
                "0.0 0.0 0.0\n"
                "0.1 0.1 0.316227766\n",
                encoding="utf-8",
            )

            system_dir = work_root / "Ag5"
            system_dir.mkdir()
            result = self.run_plot(datafile, work_root, system_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(
                (work_root / "MSD_png" / "Ag5_msd_rmsd.png").is_file()
            )


if __name__ == "__main__":
    unittest.main()
