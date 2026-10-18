"""
用途：验证 AIMD 脚本入口不会混用另一安装目录中的 Python 模块。

基本用法：
  python -m unittest discover -s AIMD/tests -p "test_*.py"

参数说明：
  无命令行参数；测试在临时目录中构造环境变量和 deploy.env。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


AIMD_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = AIMD_DIR / "scripts"
LIB_DIR = SCRIPTS_ROOT / "lib"
BOOTSTRAP_COMMAND = (
    "import sys; "
    "sys.path.insert(0, sys.argv[1]); "
    "from bootstrap import init_imports; "
    "print(init_imports())"
)


class BootstrapTests(unittest.TestCase):
    """覆盖脚本安装根一致性检查。"""

    def run_bootstrap(self, **environment: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env.pop("AIMD_SCRIPTS_ROOT", None)
        env.pop("AIMD_DEPLOY_ENV", None)
        env.update(environment)
        return subprocess.run(
            [sys.executable, "-c", BOOTSTRAP_COMMAND, str(LIB_DIR)],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_matching_scripts_root_is_accepted(self) -> None:
        result = self.run_bootstrap(AIMD_SCRIPTS_ROOT=str(SCRIPTS_ROOT))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()), SCRIPTS_ROOT)

    def test_mismatched_scripts_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            other_root = Path(temp_dir) / "other-scripts"
            result = self.run_bootstrap(AIMD_SCRIPTS_ROOT=str(other_root))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AIMD_SCRIPTS_ROOT", result.stderr)
        self.assertIn(str(other_root), result.stderr)
        self.assertIn(str(SCRIPTS_ROOT), result.stderr)

    def test_mismatched_root_loaded_from_deploy_env_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            other_root = temp / "other-scripts"
            deploy_env = temp / "deploy.env"
            deploy_env.write_text(
                f"export AIMD_SCRIPTS_ROOT={other_root}\n",
                encoding="utf-8",
            )
            result = self.run_bootstrap(AIMD_DEPLOY_ENV=str(deploy_env))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AIMD_SCRIPTS_ROOT", result.stderr)
        self.assertIn(str(other_root), result.stderr)


if __name__ == "__main__":
    unittest.main()
