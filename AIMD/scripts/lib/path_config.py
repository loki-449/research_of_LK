"""AIMD 计算工作路径配置：与脚本安装路径完全分离。"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ENV_WORK_ROOT = "AIMD_WORK_ROOT"
ENV_SCRIPTS_ROOT = "AIMD_SCRIPTS_ROOT"
ENV_DEPLOY_ENV = "AIMD_DEPLOY_ENV"
ENV_PYTHON = "AIMD_PYTHON"

RESULT_DAT_DIR = "MSD_data_for_origin"
RESULT_PNG_DIR = "MSD_png"
SKIP_DIR_NAMES = frozenset({RESULT_DAT_DIR, RESULT_PNG_DIR, "example"})


def scripts_root() -> Path:
    """脚本包安装根目录（AIMD/scripts/）。"""
    env = os.environ.get(ENV_SCRIPTS_ROOT)
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def load_deploy_env(env_file: str | Path | None = None) -> Path | None:
    """从 deploy.env 加载环境变量（已存在的变量不覆盖）。"""
    path = Path(env_file or os.environ.get(ENV_DEPLOY_ENV) or "")
    if not path.is_file():
        return None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if line.startswith("source ") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
    return path.resolve()


def resolve_work_root(cli_value: str | None = None) -> Path:
    """解析计算工作根：CLI > AIMD_WORK_ROOT > cwd。"""
    if cli_value:
        return Path(cli_value).expanduser().resolve()
    env = os.environ.get(ENV_WORK_ROOT)
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def add_work_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--work-root",
        default=None,
        help=(
            "AIMD 计算工作根（其下为 <A>/{opt,scf-MD,AIMD}/）。"
            f"未指定时读环境变量 {ENV_WORK_ROOT}，再否则使用当前工作目录。"
        ),
    )


def work_root_from_args(args: argparse.Namespace) -> Path:
    return resolve_work_root(getattr(args, "work_root", None))
