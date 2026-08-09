#!/usr/bin/env python3
"""
test_vasp_common.py — VASP 公共模块回归测试。

基本用法:
  python3 -m unittest discover -s vasp/tests -v

参数说明:
  无命令行参数；测试仅使用 Python 标准库和临时目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vasp_common import cat_potcar_in_order  # noqa: E402


class CatPotcarInOrderTests(unittest.TestCase):
    """验证 POTCAR 拼接成功与失败时的文件一致性。"""

    def test_missing_single_preserves_existing_potcar(self) -> None:
        """缺少后续单元素文件时，不得截断已有 POTCAR。"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            final = target / "POTCAR"
            original = b"existing-valid-potcar\n"
            final.write_bytes(original)
            (target / "H.POTCAR").write_bytes(b"hydrogen\n")

            with self.assertRaises(FileNotFoundError):
                cat_potcar_in_order(["H", "O"], target)

            self.assertEqual(final.read_bytes(), original)
            self.assertEqual(list(target.glob(".POTCAR.*.tmp")), [])

    def test_read_error_preserves_existing_potcar(self) -> None:
        """拼接期间发生读取错误时，不得截断已有 POTCAR。"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            final = target / "POTCAR"
            original = b"existing-valid-potcar\n"
            final.write_bytes(original)
            hydrogen = target / "H.POTCAR"
            oxygen = target / "O.POTCAR"
            hydrogen.write_bytes(b"hydrogen\n")
            oxygen.write_bytes(b"oxygen\n")
            real_read_bytes = Path.read_bytes

            def fail_on_oxygen(path: Path) -> bytes:
                if path == oxygen:
                    raise OSError("simulated read failure")
                return real_read_bytes(path)

            with mock.patch.object(Path, "read_bytes", fail_on_oxygen):
                with self.assertRaisesRegex(OSError, "simulated read failure"):
                    cat_potcar_in_order(["H", "O"], target)

            self.assertEqual(final.read_bytes(), original)
            self.assertEqual(list(target.glob(".POTCAR.*.tmp")), [])

    def test_success_replaces_target_and_removes_singles(self) -> None:
        """全部单元素文件有效时，按顺序替换目标并清理中间文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "POTCAR").write_bytes(b"old\n")
            (target / "H.POTCAR").write_bytes(b"hydrogen\n")
            (target / "O.POTCAR").write_bytes(b"oxygen\n")

            result = cat_potcar_in_order(["H", "O"], target)

            self.assertEqual(result, target / "POTCAR")
            self.assertEqual(result.read_bytes(), b"hydrogen\noxygen\n")
            self.assertFalse((target / "H.POTCAR").exists())
            self.assertFalse((target / "O.POTCAR").exists())


if __name__ == "__main__":
    unittest.main()
