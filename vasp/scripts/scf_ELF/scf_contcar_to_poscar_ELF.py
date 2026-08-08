#!/usr/bin/env python3
"""
scf_contcar_to_poscar_ELF.py — 从 opt 的 CONTCAR 复制到 scf_ELF 并改名为 POSCAR

工作流:
  <work_root>/<A>/<B>/opt/CONTCAR  →  <work_root>/<A>/<B>/scf_ELF/POSCAR

基本用法:
  python scf_contcar_to_poscar_ELF.py --scan --work-root /path/to/calc
  python scf_contcar_to_poscar_ELF.py --system-dir /path/to/calc/Ag/50
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from bootstrap import init_imports

init_imports()

from path_config import add_work_root_argument, work_root_from_args
from scf_common import SCF_SUBDIR, setup_scf_scripts
from vasp_common import OPT_SUBDIR, iter_opt_input_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy CONTCAR from opt → scf_ELF, rename to POSCAR for SCF+ELF."
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Batch mode: scan work root for all CONTCAR → copy to sibling scf_ELF",
    )
    add_work_root_argument(parser)
    parser.add_argument(
        "--contcar",
        help="Direct path to a single CONTCAR (use with --output)",
    )
    parser.add_argument(
        "--output",
        help="Target POSCAR path (use with --contcar)",
    )
    parser.add_argument(
        "--system-dir",
        help="Single system base dir, e.g. /calc/Ag/50",
    )
    parser.add_argument(
        "--opt-dir",
        dest="system_dir",
        help="Deprecated alias for --system-dir",
    )
    parser.add_argument(
        "--write-pbs",
        action="store_true",
        help="Also write scf ELF.pbs (LELF=TRUE) in scf_ELF/ if not present",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without executing",
    )
    return parser


def read_valid_contcar(contcar: Path) -> bytes:
    """读取并校验完整 CONTCAR，避免用空文件或半成品覆盖既有 POSCAR。"""
    try:
        content = contcar.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read CONTCAR: {exc}") from exc

    if not content.strip():
        raise ValueError("CONTCAR is empty")

    lines = content.decode("utf-8", errors="replace").splitlines()
    if len(lines) < 8:
        raise ValueError(f"CONTCAR is incomplete: only {len(lines)} lines")

    try:
        scale = float(lines[1].strip())
        lattice = [
            [float(value) for value in lines[index].split()[:3]]
            for index in range(2, 5)
        ]
    except (ValueError, IndexError) as exc:
        raise ValueError("CONTCAR has an invalid scale or lattice") from exc
    if (
        not math.isfinite(scale)
        or scale == 0
        or any(len(vector) != 3 for vector in lattice)
        or any(not math.isfinite(value) for vector in lattice for value in vector)
    ):
        raise ValueError("CONTCAR has an invalid scale or lattice")

    def parse_counts(line: str) -> list[int]:
        values = line.split()
        if not values:
            raise ValueError
        counts = [int(value) for value in values]
        if any(count < 0 for count in counts) or sum(counts) == 0:
            raise ValueError
        return counts

    # VASP 4 格式第 6 行直接为原子数；VASP 5+ 第 6 行为元素、第 7 行为原子数。
    try:
        counts = parse_counts(lines[5])
        mode_index = 6
    except ValueError:
        try:
            counts = parse_counts(lines[6])
        except ValueError as exc:
            raise ValueError("CONTCAR has invalid atom counts") from exc
        if len(lines[5].split()) != len(counts):
            raise ValueError("CONTCAR element and atom-count columns differ")
        mode_index = 7

    if lines[mode_index].strip().lower().startswith("s"):
        mode_index += 1
    if mode_index >= len(lines) or not lines[mode_index].strip().lower().startswith(
        ("d", "c", "k")
    ):
        raise ValueError("CONTCAR has no valid coordinate mode")

    coordinate_start = mode_index + 1
    atom_count = sum(counts)
    if len(lines) < coordinate_start + atom_count:
        raise ValueError(
            f"CONTCAR is incomplete: expected {atom_count} atomic coordinates"
        )
    try:
        coordinates = [
            [float(value) for value in lines[index].split()[:3]]
            for index in range(coordinate_start, coordinate_start + atom_count)
        ]
    except ValueError as exc:
        raise ValueError("CONTCAR has invalid atomic coordinates") from exc
    if any(len(vector) != 3 for vector in coordinates) or any(
        not math.isfinite(value) for vector in coordinates for value in vector
    ):
        raise ValueError("CONTCAR has invalid atomic coordinates")

    return content


def atomic_write_poscar(content: bytes, poscar: Path) -> None:
    """同目录临时写入后原子替换，写入失败时保留既有 POSCAR。"""
    poscar.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{poscar.name}.", dir=poscar.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, poscar)
    finally:
        temp_path.unlink(missing_ok=True)


def copy_contcar_to_poscar(
    contcar: Path,
    poscar: Path,
    write_pbs: bool = False,
    dry_run: bool = False,
) -> bool:
    contcar = Path(contcar)
    poscar = Path(poscar)

    if not contcar.is_file():
        print(f"  ERROR: CONTCAR not found: {contcar}")
        return False

    try:
        content = read_valid_contcar(contcar)
    except ValueError as exc:
        print(f"  ERROR: refusing to replace {poscar}: {exc}")
        return False

    if dry_run:
        print(f"  [dry-run] cp {contcar}")
        print(f"  [dry-run]   → {poscar}")
        if write_pbs:
            print(f"  [dry-run] write {poscar.parent}/ELF.pbs (LELF=TRUE)")
        return True

    atomic_write_poscar(content, poscar)
    print(f"  CONTCAR → {poscar}")

    if write_pbs:
        setup_scf_scripts(poscar.parent.parent)
        print(f"  ELF.pbs written in {poscar.parent}/ (LELF=TRUE)")

    return True


def process_single_system(
    base_dir: Path,
    write_pbs: bool = False,
    dry_run: bool = False,
) -> bool:
    contcar = base_dir / OPT_SUBDIR / "CONTCAR"
    poscar = base_dir / SCF_SUBDIR / "POSCAR"

    print(f"Processing: {base_dir}")
    print(f"  from: {contcar}")
    print(f"  to:   {poscar}")

    return copy_contcar_to_poscar(contcar, poscar, write_pbs=write_pbs, dry_run=dry_run)


def batch_scan(
    work_root: Path,
    write_pbs: bool = False,
    dry_run: bool = False,
) -> int:
    work_root = Path(work_root)

    contcar_files = iter_opt_input_files(work_root, "CONTCAR")
    if not contcar_files:
        print(f"No {OPT_SUBDIR}/CONTCAR found under {work_root}")
        return 1

    ok = 0
    for contcar in contcar_files:
        try:
            rel = contcar.relative_to(work_root)
        except ValueError:
            rel = contcar

        base_dir = work_root / rel.parent.parent
        poscar = base_dir / SCF_SUBDIR / "POSCAR"

        print("---------------------------")
        print(f"System: {base_dir.relative_to(work_root)}")
        print(f"  CONTCAR: {contcar}")

        if copy_contcar_to_poscar(contcar, poscar, write_pbs=write_pbs, dry_run=dry_run):
            ok += 1

    print("---------------------------")
    print(f"Finished: {ok}/{len(contcar_files)} systems processed.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.scan:
        work_root = work_root_from_args(args)
        print(f"Work root: {work_root}")
        return batch_scan(work_root, write_pbs=args.write_pbs, dry_run=args.dry_run)

    if args.contcar and args.output:
        poscar = Path(args.output)
        if poscar.name != "POSCAR":
            poscar = poscar.parent / "POSCAR"
        ok = copy_contcar_to_poscar(
            Path(args.contcar), poscar,
            write_pbs=args.write_pbs,
            dry_run=args.dry_run,
        )
        return 0 if ok else 1

    if args.system_dir:
        ok = process_single_system(
            Path(args.system_dir),
            write_pbs=args.write_pbs,
            dry_run=args.dry_run,
        )
        return 0 if ok else 1

    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
