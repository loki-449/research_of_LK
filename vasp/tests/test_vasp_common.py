#!/usr/bin/env python3
"""
test_vasp_common.py — VASP 公共模块回归测试

用途:
  验证赝势候选择优不会因空文件崩溃或选中无效 POTCAR。

基本用法:
  python3 -m unittest discover -s vasp/tests -v

参数:
  无。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import (  # noqa: E402
    parse_potcar_date,
    parse_potcar_date_str,
    select_best_potcar_file,
)


class PotcarSelectionTests(unittest.TestCase):
    """验证损坏候选不会中断或污染 POTCAR 择优。"""

    def test_empty_candidate_is_skipped_when_valid_candidate_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            empty_dir = root / "Fe"
            valid_dir = root / "Fe_pv"
            empty_dir.mkdir()
            valid_dir.mkdir()
            (empty_dir / "POTCAR").write_bytes(b"")
            valid = valid_dir / "POTCAR"
            valid.write_text(
                "PAW_PBE Fe_pv 06Sep2000\n"
                "   ZVAL   = 14.000\n",
                encoding="utf-8",
            )

            selected = select_best_potcar_file([empty_dir, valid_dir])

            self.assertEqual(selected, valid)

    def test_only_invalid_candidates_return_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            empty_dir = root / "Fe"
            missing_zval_dir = root / "Fe_pv"
            malformed_dir = root / "Fe_sv"
            empty_dir.mkdir()
            missing_zval_dir.mkdir()
            malformed_dir.mkdir()
            (empty_dir / "POTCAR").write_bytes(b"")
            (missing_zval_dir / "POTCAR").write_text(
                "PAW_PBE Fe_pv 06Sep2000\n",
                encoding="utf-8",
            )
            (malformed_dir / "POTCAR").write_text(
                "PAW_PBE Fe_sv 06Sep2000\n"
                "   ZVAL   = .\n",
                encoding="utf-8",
            )

            selected = select_best_potcar_file(
                [empty_dir, missing_zval_dir, malformed_dir]
            )

            self.assertIsNone(selected)

    def test_selection_prefers_zval_then_newest_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specifications = (
                ("Fe", 8.0, "01Jan2099"),
                ("Fe_pv", 14.0, "01Jan2000"),
                ("Fe_sv", 14.0, "01Jan2024"),
            )
            candidates = []
            for name, zval, date in specifications:
                candidate = root / name
                candidate.mkdir()
                (candidate / "POTCAR").write_text(
                    f"PAW_PBE {name} {date}\n"
                    f"   ZVAL   = {zval:.3f}\n",
                    encoding="utf-8",
                )
                candidates.append(candidate)

            selected = select_best_potcar_file(candidates)

            self.assertEqual(selected, candidates[-1] / "POTCAR")

    def test_empty_potcar_date_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            potcar = Path(tmp) / "POTCAR"
            potcar.write_bytes(b"")

            self.assertEqual(parse_potcar_date(potcar), datetime.min)
            self.assertEqual(parse_potcar_date_str(potcar), "unknown")


if __name__ == "__main__":
    unittest.main()
