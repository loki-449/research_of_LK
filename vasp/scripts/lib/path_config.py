"""计算工作路径配置：与脚本安装路径完全分离。"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ENV_WORK_ROOT = "VASP_WORK_ROOT"
ENV_SCRIPTS_ROOT = "VASP_SCRIPTS_ROOT"
ENV_DEPLOY_ENV = "VASP_DEPLOY_ENV"
ENV_PBE_LIB = "PBE_LIB"
ENV_PYTHON = "VASP_PYTHON"
ENV_SUBMIT_MAX_JOBS = "VASP_SUBMIT_MAX_JOBS"
ENV_SUBMIT_WAIT_INTERVAL = "VASP_SUBMIT_WAIT_INTERVAL"


def scripts_root() -> Path:
    """脚本包安装根目录（vasp/scripts/）。"""
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
    """解析计算工作根目录：CLI > 环境变量 > 当前工作目录。"""
    if cli_value:
        return Path(cli_value).expanduser().resolve()
    env = os.environ.get(ENV_WORK_ROOT)
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def add_work_root_argument(parser: argparse.ArgumentParser) -> None:
    """为 argparse 添加 --work-root 及已废弃别名。"""
    parser.add_argument(
        "--work-root",
        default=None,
        help=(
            "计算工作根目录（其下为 <材料>/<压强>/opt|scf_ELF）。"
            f"未指定时读取环境变量 {ENV_WORK_ROOT}，再否则使用当前工作目录。"
        ),
    )
    parser.add_argument("--vasp-root", dest="work_root", help=argparse.SUPPRESS)
    parser.add_argument("--opt-root", dest="work_root", help=argparse.SUPPRESS)
    parser.add_argument("--elf-root", dest="work_root", help=argparse.SUPPRESS)


def work_root_from_args(args: argparse.Namespace) -> Path:
    """从 parse_args 结果得到绝对工作根路径。"""
    return resolve_work_root(getattr(args, "work_root", None))


def script_path(module: str, name: str) -> Path:
    """返回已安装脚本的路径，module 为 opt 或 scf_ELF。"""
    return scripts_root() / module / name


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
