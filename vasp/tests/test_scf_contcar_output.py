#!/usr/bin/env python3
"""
test_scf_contcar_output.py — CONTCAR 单文件复制输出路径回归测试。

用途:
  验证 --output 严格写入用户指定路径，不会静默改写为同目录 POSCAR
  并覆盖已有正式结构。

基本用法:
  python3 -m unittest vasp/tests/test_scf_contcar_output.py -v

参数说明:
  无。测试仅使用标准库与临时目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "scf_ELF"
sys.path.insert(0, str(SCRIPT_DIR))

from scf_contcar_to_poscar_ELF import main  # noqa: E402


class ExplicitOutputPathTests(unittest.TestCase):
    """验证显式输出路径不会被脚本替换 basename。"""

    def test_non_poscar_output_is_respected(self) -> None:
        """自定义输出应写入指定文件，并保留同目录已有 POSCAR。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contcar = root / "CONTCAR"
            output = root / "preview.vasp"
            official_poscar = root / "POSCAR"
            contcar.write_text("new optimized structure\n", encoding="utf-8")
            official_poscar.write_text("existing official structure\n", encoding="utf-8")

            result = main(
                ["--contcar", str(contcar), "--output", str(output)]
            )

            self.assertEqual(result, 0)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "new optimized structure\n",
            )
            self.assertEqual(
                official_poscar.read_text(encoding="utf-8"),
                "existing official structure\n",
            )


if __name__ == "__main__":
    unittest.main()
