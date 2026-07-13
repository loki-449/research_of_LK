#!/usr/bin/env python3
"""
submit_opt_elf.py — 批量提交 opt_ELF 目录下的 PBS 任务

用途:
  遍历 vasp/opt 根目录下所有 opt_ELF/ 文件夹，对尚未提交的任务:
    1. chmod +x ELF.pbs
    2. qsub ELF.pbs

  通过标记文件避免重复提交；--resubmit 可清除旧标记后重新提交。

队列控制:
  仅当当前用户 PBS 任务数 <= --max-jobs（默认 8）时提交；
  若队列已满，自动等待 --wait-interval 秒后重试，直到有空位继续提交。
  加 --no-wait 则队列满时立即退出（旧行为）。

依赖:
  Linux HPC 环境，需可用 qstat / qsub

基本用法:
  python submit_opt_elf.py ./vasp/opt
  python submit_opt_elf.py ./vasp/opt --max-jobs 8
  python submit_opt_elf.py ./vasp/opt --resubmit          # 清除标记后重新提交
  python submit_opt_elf.py ./vasp/opt --clear-markers     # 仅删除标记，不提交
  python submit_opt_elf.py ./vasp/opt --dry-run

推荐工作流:
  python setup_elf_workflow.py /path/to/QE_folder
  python make_poscar.py --scan /path/to/QE_folder --elf-root ./vasp/opt
  python make_potcar.py --scan ./vasp/opt
  python submit_opt_elf.py ./vasp/opt
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from vasp_common import OPT_SUBDIR

MARKER_NAME = ".pbs_submitted"
PBS_SCRIPT = "ELF.pbs"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch submit PBS jobs in all opt_ELF directories."
    )
    parser.add_argument(
        "elf_root",
        nargs="?",
        default="./vasp/opt",
        help="Root directory (default: ./vasp/opt)",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=8,
        help="Submit only when user job count <= this value (default: 8)",
    )
    parser.add_argument(
        "--wait-interval",
        type=int,
        default=60,
        help="Seconds to wait when queue is full before retry (default: 60)",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Exit immediately when queue is full instead of waiting",
    )
    parser.add_argument(
        "--resubmit",
        action="store_true",
        help="Clear submission markers before submitting",
    )
    parser.add_argument(
        "--clear-markers",
        action="store_true",
        help="Only remove submission markers, do not submit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without chmod/qsub",
    )
    return parser


def find_opt_elf_dirs(elf_root: Path) -> List[Path]:
    """Find all opt_ELF directories containing ELF.pbs."""
    root = Path(elf_root)
    if not root.is_dir():
        raise FileNotFoundError(f"Root not found: {root}")

    dirs = []
    for opt_dir in sorted(root.rglob(OPT_SUBDIR)):
        if opt_dir.is_dir() and (opt_dir / PBS_SCRIPT).is_file():
            dirs.append(opt_dir)
    return dirs


def marker_path(opt_dir: Path) -> Path:
    return opt_dir / MARKER_NAME


def read_marker(opt_dir: Path) -> Optional[str]:
    mp = marker_path(opt_dir)
    if not mp.is_file():
        return None
    return mp.read_text(encoding="utf-8", errors="replace").strip()


def write_marker(opt_dir: Path, job_id: str) -> None:
    content = (
        f"job_id={job_id}\n"
        f"submitted_at={datetime.now().isoformat(timespec='seconds')}\n"
        f"script={PBS_SCRIPT}\n"
    )
    marker_path(opt_dir).write_text(content, encoding="utf-8")


def clear_markers(elf_root: Path) -> int:
    count = 0
    for opt_dir in find_opt_elf_dirs(elf_root):
        mp = marker_path(opt_dir)
        if mp.is_file():
            mp.unlink()
            print(f"  cleared: {mp}")
            count += 1
    return count


def count_user_jobs() -> int:
    """Return approximate number of PBS jobs for current user."""
    user = os.environ.get("USER") or os.environ.get("USERNAME")
    if not user:
        return 0

    try:
        result = subprocess.run(
            ["qstat", "-u", user],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise RuntimeError("qstat not found; run this script on a PBS cluster")

    if result.returncode != 0:
        return 0

    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    if len(lines) <= 2:
        return 0
    return len(lines) - 2


def jobs_within_limit(max_jobs: int) -> Tuple[bool, int]:
    n = count_user_jobs()
    return n <= max_jobs, n


def chmod_executable(script: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] chmod +x {script}")
        return
    script.chmod(script.stat().st_mode | 0o111)


def qsub_job(opt_dir: Path, dry_run: bool) -> str:
    script = opt_dir / PBS_SCRIPT
    if dry_run:
        print(f"  [dry-run] qsub {script} (cwd={opt_dir})")
        return "dry-run"

    result = subprocess.run(
        ["qsub", PBS_SCRIPT],
        cwd=opt_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"qsub failed in {opt_dir}: {err}")

    job_id = result.stdout.strip().split()[0] if result.stdout.strip() else "unknown"
    return job_id


def wait_for_slot(
    max_jobs: int,
    wait_interval: int,
    no_wait: bool,
    dry_run: bool,
) -> Optional[int]:
    """Wait until user job count <= max_jobs. Returns job count, or None if giving up."""
    while True:
        ok, n_jobs = jobs_within_limit(max_jobs)
        if ok:
            return n_jobs
        if no_wait or dry_run:
            return None
        print(
            f"  WAIT: user job count {n_jobs} > {max_jobs}, "
            f"retry in {wait_interval}s ..."
        )
        time.sleep(wait_interval)


def submit_all(
    elf_root: Path,
    max_jobs: int,
    wait_interval: int,
    no_wait: bool,
    resubmit: bool,
    clear_only: bool,
    dry_run: bool,
) -> int:
    if resubmit or clear_only:
        n_cleared = clear_markers(elf_root)
        print(f"Cleared {n_cleared} marker(s) under {elf_root}")
        if clear_only:
            return 0

    opt_dirs = find_opt_elf_dirs(elf_root)
    if not opt_dirs:
        print(f"No {OPT_SUBDIR}/{PBS_SCRIPT} found under {elf_root}")
        return 1

    submitted = 0
    skipped = 0
    stopped = 0

    for opt_dir in opt_dirs:
        try:
            rel = opt_dir.relative_to(elf_root)
        except ValueError:
            rel = opt_dir
        print(f"Processing: {rel}")

        if read_marker(opt_dir) and not resubmit:
            print(f"  SKIP: already submitted ({marker_path(opt_dir)})")
            skipped += 1
            continue

        n_jobs = wait_for_slot(max_jobs, wait_interval, no_wait, dry_run)
        if n_jobs is None:
            _, n_jobs = jobs_within_limit(max_jobs)
            print(
                f"  STOP: user job count {n_jobs} > {max_jobs} "
                f"(qstat -u $USER check)"
            )
            stopped += 1
            break

        try:
            chmod_executable(opt_dir / PBS_SCRIPT, dry_run=dry_run)
            job_id = qsub_job(opt_dir, dry_run=dry_run)
            if not dry_run:
                write_marker(opt_dir, job_id)
            print(f"  SUBMITTED: job {job_id}  (user jobs before submit: {n_jobs})")
            submitted += 1
        except (OSError, RuntimeError) as exc:
            print(f"  ERROR: {exc}")

        print("---------------------------")

    print(
        f"Done: submitted={submitted}, skipped={skipped}, "
        f"stopped_at_limit={stopped}, total={len(opt_dirs)}"
    )
    if submitted or (skipped and not stopped):
        return 0
    return 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return submit_all(
        Path(args.elf_root),
        max_jobs=args.max_jobs,
        wait_interval=args.wait_interval,
        no_wait=args.no_wait,
        resubmit=args.resubmit,
        clear_only=args.clear_markers,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
