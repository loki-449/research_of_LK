#!/usr/bin/env python3
"""
test_make_potcar_output.py — POTCAR 显式输出路径回归测试。

用途:
  验证 opt 目录中的自定义输出文件名会被严格保留，不会覆盖正式
  POTCAR 或已有 opt.pbs。

基本用法:
  python3 -m unittest vasp/tests/test_make_potcar_output.py -v

参数说明:
  无。测试仅使用标准库与临时目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "opt"
sys.path.insert(0, str(SCRIPT_DIR))

from make_potcar import main  # noqa: E402


class ExplicitOutputPathTests(unittest.TestCase):
    """验证 --output 不会被 opt 目录规则静默改写。"""

    def test_custom_output_in_opt_is_respected(self) -> None:
        """候选 POTCAR 应写入指定文件，并保留正式输入与 PBS 脚本。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            opt_dir = root / "calc" / "H" / "100" / "opt"
            opt_dir.mkdir(parents=True)

            poscar = opt_dir / "POSCAR"
            poscar.write_text(
                "H\n1.0\n1 0 0\n0 1 0\n0 0 1\nH\n1\nDirect\n0 0 0\n",
                encoding="utf-8",
            )

            official_potcar = opt_dir / "POTCAR"
            official_potcar.write_text("existing production POTCAR\n", encoding="utf-8")
            opt_pbs = opt_dir / "opt.pbs"
            opt_pbs.write_text("custom cluster settings\n", encoding="utf-8")

            pbe_lib = root / "pbe"
            element_dir = pbe_lib / "H"
            element_dir.mkdir(parents=True)
            candidate_content = "PAW_PBE H 01Jan2020\nZVAL = 1.0\n"
            (element_dir / "POTCAR").write_text(
                candidate_content,
                encoding="utf-8",
            )

            custom_output = opt_dir / "POTCAR.preview"
            result = main(
                [
                    "--poscar",
                    str(poscar),
                    "--output",
                    str(custom_output),
                    "--pbe-lib",
                    str(pbe_lib),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(
                custom_output.read_text(encoding="utf-8"),
                candidate_content,
            )
            self.assertEqual(
                official_potcar.read_text(encoding="utf-8"),
                "existing production POTCAR\n",
            )
            self.assertEqual(
                opt_pbs.read_text(encoding="utf-8"),
                "custom cluster settings\n",
            )


if __name__ == "__main__":
    unittest.main()
