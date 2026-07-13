#!/usr/bin/env bash
# AIMD 脚本包安装
# 用法: bash install.sh [目标路径]
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-/home/test1/hhy/high-317/AIMD/scripts}"
echo "Installing AIMD scripts: $SRC -> $DEST"
mkdir -p "$DEST"
cp -r "$SRC/lib" "$SRC/MSD_RMSD" "$SRC/compat" "$DEST/"
cp "$SRC/README.md" "$DEST/" 2>/dev/null || true
echo "Done. export AIMD_SCRIPTS_ROOT=$DEST"
