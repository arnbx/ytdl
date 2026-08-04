#!/usr/bin/env python3
"""
Generate OS-specific icon formats (ICO for Windows, ICNS for macOS)
from the PNG assets in the icon/ folder.
"""
import os
import sys
from PIL import Image

def generate_icons():
    icon_dir = "icon"
    src_png = os.path.join(icon_dir, "icon-256.png")
    
    if not os.path.exists(src_png):
        print(f"[WARN] {src_png} not found. Skipping icon conversion.")
        return

    img = Image.open(src_png)

    # 1. Windows .ico format (multi-resolution)
    ico_path = os.path.join(icon_dir, "icon.ico")
    try:
        sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, format="ICO", sizes=sizes)
        print(f"[OK] Generated Windows icon: {ico_path}")
    except Exception as e:
        print(f"[ERROR] Failed to create {ico_path}: {e}")

    # 2. macOS .icns format
    icns_path = os.path.join(icon_dir, "icon.icns")
    try:
        img.save(icns_path, format="ICNS")
        print(f"[OK] Generated macOS icon: {icns_path}")
    except Exception as e:
        print(f"[ERROR] Failed to create {icns_path}: {e}")

if __name__ == "__main__":
    generate_icons()
