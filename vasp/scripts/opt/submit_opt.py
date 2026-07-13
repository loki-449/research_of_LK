#!/usr/bin/env python3
"""
submit_opt.py — 批量提交 opt 目录下的 PBS 任务

基本用法:
  python submit_opt.py /path/to/calc
  python submit_opt.py --work-root /path/to/calc
  export VASP_WORK_ROOT=/path/to/calc && python submit_opt.py
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from bootstrap import init_imports

init_imports()

from path_config import add_work_root_argument, env_int, resolve_work_root
from path_config import ENV_SUBMIT_MAX_JOBS, ENV_SUBMIT_WAIT_INTERVAL
from vasp_common import OPT_PBS_SCRIPT, OPT_SUBDIR, iter_opt_work_dirs

MARKER_NAME = ".pbs_submitted"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch submit PBS jobs in all opt directories."
    )
    parser.add_argument(
        "work_root_pos",
        nargs="?",
        default=None,
        metavar="WORK_ROOT",
        help="计算工作根目录（也可通过 --work-root 或 VASP_WORK_ROOT 指定）",
    )
    add_work_root_argument(parser)
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=env_int(ENV_SUBMIT_MAX_JOBS, 8),
        help="Submit only when user job count <= this value (default: 8 or VASP_SUBMIT_MAX_JOBS)",
    )
    parser.add_argument(
        "--wait-interval",
        type=int,
        default=env_int(ENV_SUBMIT_WAIT_INTERVAL, 60),
        help="Seconds to wait when queue is full before retry (default: 60 or VASP_SUBMIT_WAIT_INTERVAL)",
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


def find_opt_dirs(work_root: Path) -> List[Path]:
    root = Path(work_root)
    if not root.is_dir():
        raise FileNotFoundError(f"Work root not found: {root}")

    return [
        opt_dir
        for opt_dir in iter_opt_work_dirs(root)
        if (opt_dir / OPT_PBS_SCRIPT).is_file()
    ]


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
        f"script={OPT_PBS_SCRIPT}\n"
    )
    marker_path(opt_dir).write_text(content, encoding="utf-8")


def clear_markers(work_root: Path) -> int:
    count = 0
    for opt_dir in find_opt_dirs(work_root):
        mp = marker_path(opt_dir)
        if mp.is_file():
            mp.unlink()
            print(f"  cleared: {mp}")
            count += 1
    return count


def count_user_jobs() -> int:
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
    script = opt_dir / OPT_PBS_SCRIPT
    if dry_run:
        print(f"  [dry-run] qsub {script} (cwd={opt_dir})")
        return "dry-run"

    result = subprocess.run(
        ["qsub", OPT_PBS_SCRIPT],
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
    if dry_run:
        return 0
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
    work_root: Path,
    max_jobs: int,
    wait_interval: int,
    no_wait: bool,
    resubmit: bool,
    clear_only: bool,
    dry_run: bool,
) -> int:
    if resubmit or clear_only:
        n_cleared = clear_markers(work_root)
        print(f"Cleared {n_cleared} marker(s) under {work_root}")
        if clear_only:
            return 0

    opt_dirs = find_opt_dirs(work_root)
    if not opt_dirs:
        print(f"No {OPT_SUBDIR}/{OPT_PBS_SCRIPT} found under {work_root}")
        return 1

    submitted = 0
    skipped = 0
    stopped = 0

    for opt_dir in opt_dirs:
        try:
            rel = opt_dir.relative_to(work_root)
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
            chmod_executable(opt_dir / OPT_PBS_SCRIPT, dry_run=dry_run)
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
    work_root = resolve_work_root(args.work_root or args.work_root_pos)
    print(f"Work root: {work_root}")
    return submit_all(
        work_root,
        max_jobs=args.max_jobs,
        wait_interval=args.wait_interval,
        no_wait=args.no_wait,
        resubmit=args.resubmit,
        clear_only=args.clear_markers,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
