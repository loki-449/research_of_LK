#!/usr/bin/env python3
"""
test_potcar_element_paths.py — POTCAR 元素名路径边界回归测试。

用途:
  验证来自 QE/POSCAR 的元素名不能通过路径分隔符逃出赝势库或工作目录，
  同时保留正常化学元素名的 POTCAR 组装行为。

基本用法:
  python3 -m unittest vasp/tests/test_potcar_element_paths.py -v

参数说明:
  无。测试仅使用临时目录，不读写正式计算数据。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import assemble_potcar  # noqa: E402


class PotcarElementPathTests(unittest.TestCase):
    """验证元素标识不能被解释成文件系统路径。"""

    def test_parent_component_cannot_overwrite_outside_target(self) -> None:
        """恶意元素名必须在读取赝势或写入单元素文件前被拒绝。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pbe_lib = root / "library" / "PBE"
            pbe_lib.mkdir(parents=True)
            escaped_source = root / "library" / "victim" / "POTCAR"
            escaped_source.parent.mkdir(parents=True)
            escaped_source.write_text(
                "PAW_PBE victim 01Jan2020\nZVAL = 1.0\n",
                encoding="utf-8",
            )

            target_dir = root / "calculation" / "opt"
            target_dir.mkdir(parents=True)
            outside_target = root / "calculation" / "victim.POTCAR"
            outside_target.write_text("keep me\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Invalid element"):
                assemble_potcar(
                    ["../victim"],
                    target_dir / "POTCAR",
                    pbe_lib=pbe_lib,
                )

            self.assertEqual(
                outside_target.read_text(encoding="utf-8"),
                "keep me\n",
            )
            self.assertFalse((target_dir / "POTCAR").exists())

    def test_normal_element_still_assembles_potcar(self) -> None:
        """合法化学元素名的标准组装流程保持不变。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pbe_lib = root / "PBE"
            source = pbe_lib / "H" / "POTCAR"
            source.parent.mkdir(parents=True)
            content = "PAW_PBE H 01Jan2020\nZVAL = 1.0\n"
            source.write_text(content, encoding="utf-8")

            output = root / "work" / "POTCAR"
            assemble_potcar(["H"], output, pbe_lib=pbe_lib)

            self.assertEqual(output.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
