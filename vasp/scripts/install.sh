#!/usr/bin/env bash
# VASP 脚本包安装脚本
# 用法: bash install.sh [目标路径]
# 默认: /home/test1/hhy/tools/vasp/scripts

set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-/home/test1/hhy/tools/vasp/scripts}"

echo "Installing VASP scripts:"
echo "  from: $SRC"
echo "  to:   $DEST"

mkdir -p "$DEST"
cp -r "$SRC/lib" "$SRC/opt" "$SRC/scf_ELF" "$DEST/"
cp "$SRC/README.md" "$DEST/"

echo "Done. Add to deploy.env:"
echo "  export VASP_SCRIPTS_ROOT=$DEST"
