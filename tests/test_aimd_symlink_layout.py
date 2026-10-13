#!/usr/bin/env python3
"""
测试 AIMD 逻辑体系路径在 XDATCAR 为符号链接时不会被目标路径替换。

基本用法:
  python -m unittest tests/test_aimd_symlink_layout.py

参数说明:
  无命令行参数；测试在临时目录中构造 ALIAS 与 TARGET 两个体系。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "AIMD" / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "AIMD" / "scripts" / "MSD_RMSD"))

from extract_msd_flex import extract_one
from msd_common import published_dat_path, system_dir_from_xdatcar


XDATCAR = """Alias trajectory
1.0
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
H
1
Direct configuration= 1
0.0 0.0 0.0
Direct configuration= 2
0.1 0.0 0.0
"""


class AimdSymlinkLayoutTest(unittest.TestCase):
    """验证提取和发布均采用用户传入的逻辑体系目录。"""

    def test_extract_uses_alias_identity_and_incar(self) -> None:
        """符号链接轨迹应发布到 ALIAS，并读取 ALIAS/AIMD/INCAR。"""
        with tempfile.TemporaryDirectory() as tmp:
            work_root = Path(tmp)
            alias_aimd = work_root / "ALIAS" / "AIMD"
            target_aimd = work_root / "TARGET" / "AIMD"
            alias_aimd.mkdir(parents=True)
            target_aimd.mkdir(parents=True)

            target_xdatcar = target_aimd / "XDATCAR"
            target_xdatcar.write_text(XDATCAR, encoding="utf-8")
            (target_aimd / "INCAR").write_text("POTIM = 9.0\n", encoding="utf-8")
            (alias_aimd / "INCAR").write_text("POTIM = 2.0\n", encoding="utf-8")

            alias_xdatcar = alias_aimd / "XDATCAR"
            alias_xdatcar.symlink_to(target_xdatcar)
            (alias_aimd / "nested").mkdir()
            dotted_alias_xdatcar = alias_aimd / "nested" / ".." / "XDATCAR"

            self.assertEqual(
                system_dir_from_xdatcar(dotted_alias_xdatcar),
                work_root / "ALIAS",
            )
            self.assertTrue(
                extract_one(
                    dotted_alias_xdatcar,
                    work_root,
                    dt=None,
                    output=None,
                    stride=1,
                    elements=None,
                    element_order="file",
                    keep_local=False,
                    no_publish=False,
                    dry_run=False,
                )
            )

            alias_dat = published_dat_path(work_root, "ALIAS")
            target_dat = published_dat_path(work_root, "TARGET")
            self.assertTrue(alias_dat.is_file())
            self.assertFalse(target_dat.exists())

            rows = [
                line.split()
                for line in alias_dat.read_text(encoding="utf-8").splitlines()
                if not line.startswith("#")
            ]
            self.assertEqual(float(rows[1][0]), 0.002)


if __name__ == "__main__":
    unittest.main()
