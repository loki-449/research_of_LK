#!/usr/bin/env python3
"""Remove xcursor.png from every ELF folder"""
import os, sys

ELF_ROOT = sys.argv[1] if len(sys.argv) > 1 else "./ELF"

removed = 0
for root, dirs, files in os.walk(ELF_ROOT):
    for f in files:
        if f == "xcursor.png":
            path = os.path.join(root, f)
            os.remove(path)
            removed += 1
            print(f"  removed: {path}")

print(f"Done: {removed} xcursor.png files removed")
