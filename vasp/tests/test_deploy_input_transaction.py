#!/usr/bin/env python3
"""
用途：验证 VASP 一键部署不会在 POTCAR 生成失败时留下新旧输入混用。

基本用法：
  python3 -m unittest vasp/tests/test_deploy_input_transaction.py -v

参数说明：
  无命令行参数；测试仅使用标准库与临时目录。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from scf_common import SCF_PBS_SCRIPT, deploy_scf_system  # noqa: E402
from vasp_common import OPT_PBS_SCRIPT, deploy_opt_system  # noqa: E402


def write_relax_input(path: Path, element: str = "He") -> None:
    """写入一个最小的 QE 结构输入。"""
    path.write_text(
        f"""&SYSTEM
  ibrav = 0,
  nat = 1,
  ntyp = 1,
/
CELL_PARAMETERS angstrom
1 0 0
0 1 0
0 0 1
ATOMIC_POSITIONS crystal
{element} 0 0 0
K_POINTS gamma
""",
        encoding="utf-8",
    )


class DeployInputTransactionTests(unittest.TestCase):
    """覆盖 opt 与 scf_ELF 完整部署的失败一致性。"""

    def test_missing_potcar_preserves_all_existing_inputs(self) -> None:
        """缺少新元素赝势时，旧 PBS、POSCAR 与 POTCAR 必须成套保留。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = root / "relax.in"
            pbe_lib = root / "pbe"
            pbe_lib.mkdir()
            write_relax_input(relax_in)

            cases = (
                ("opt", OPT_PBS_SCRIPT, deploy_opt_system),
                ("scf_ELF", SCF_PBS_SCRIPT, deploy_scf_system),
            )
            for subdir, pbs_name, deploy in cases:
                with self.subTest(subdir=subdir):
                    base_dir = root / subdir / "system"
                    target_dir = base_dir / subdir
                    target_dir.mkdir(parents=True)
                    expected = {
                        pbs_name: b"old pbs\n",
                        "POSCAR": b"old structure\n",
                        "POTCAR": b"old pseudopotential\n",
                    }
                    for filename, content in expected.items():
                        (target_dir / filename).write_bytes(content)

                    with self.assertRaises(FileNotFoundError):
                        deploy(relax_in, base_dir, pbe_lib=pbe_lib)

                    for filename, content in expected.items():
                        self.assertEqual((target_dir / filename).read_bytes(), content)
                    self.assertEqual(list(target_dir.glob(".deploy-*")), [])

    def test_success_replaces_complete_input_set(self) -> None:
        """赝势可用时，正式目录中的三项输入应一起更新。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relax_in = root / "relax.in"
            pbe_lib = root / "pbe"
            potcar_dir = pbe_lib / "H"
            potcar_dir.mkdir(parents=True)
            write_relax_input(relax_in, element="H")
            potcar = b"PAW_PBE H 01Jan2024\n   ZVAL = 1.000\n"
            (potcar_dir / "POTCAR").write_bytes(potcar)

            cases = (
                ("opt", OPT_PBS_SCRIPT, deploy_opt_system),
                ("scf_ELF", SCF_PBS_SCRIPT, deploy_scf_system),
            )
            for subdir, pbs_name, deploy in cases:
                with self.subTest(subdir=subdir):
                    base_dir = root / subdir / "system"
                    deploy(relax_in, base_dir, pbe_lib=pbe_lib)
                    target_dir = base_dir / subdir

                    self.assertIn("H", (target_dir / "POSCAR").read_text())
                    self.assertEqual((target_dir / "POTCAR").read_bytes(), potcar)
                    self.assertTrue((target_dir / pbs_name).is_file())
                    self.assertEqual(list(target_dir.glob(".deploy-*")), [])


if __name__ == "__main__":
    unittest.main()
