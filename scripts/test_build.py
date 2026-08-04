#!/usr/bin/env python3
"""
Automated Build Verification Script (Cross-Platform)

Verifies:
1. PyInstaller output binary exists and has non-zero size.
2. Zero Python source files (.py) are present in the bundled package directory (only .pyc / bytecode).
3. Executable launches successfully with `--check-build` and returns exit code 0.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def main():
    print("=" * 70)
    print("YTDL Automated Cross-Platform Build Verification")
    print("=" * 70)

    is_windows = platform.system().lower() == "windows"
    dist_dir = Path("dist")

    if not dist_dir.exists():
        print(f"[ERROR] Build directory '{dist_dir}' does not exist.")
        sys.exit(1)

    if is_windows:
        target_exe = dist_dir / "YTDL.exe"
    elif platform.system().lower() == "darwin":
        target_exe = dist_dir / "YTDL.app" / "Contents" / "MacOS" / "YTDL"
        if not target_exe.exists():
            target_exe = dist_dir / "YTDL" / "YTDL"
    else:
        target_exe = dist_dir / "YTDL" / "YTDL"

    print(f"[*] Checking for executable: {target_exe}")
    if not target_exe.exists():
        print(f"[ERROR] Target executable '{target_exe}' was not found.")
        sys.exit(1)

    stat = target_exe.stat()
    print(f"[+] Executable found! Size: {stat.st_size / (1024*1024):.2f} MB")
    if stat.st_size == 0:
        print("[ERROR] Executable file is 0 bytes!")
        sys.exit(1)

    # For one-dir builds (Linux & macOS), verify zero .py source files exist in package directory
    if not is_windows:
        pkg_dir = dist_dir / "YTDL"
        print(f"[*] Scanning package directory '{pkg_dir}' for leaked .py source files...")
        py_files = list(pkg_dir.rglob("*.py"))
        if py_files:
            print(f"[ERROR] Found {len(py_files)} unexpected .py source files in package directory:")
            for pf in py_files:
                print(f"    - {pf}")
            sys.exit(1)
        print("[+] Zero .py source files present in bundled directory (bytecode only!).")

    # Verify execution of built binary with --check-build flag
    print(f"[*] Invoking binary with --check-build flag...")
    try:
        cmd = [str(target_exe.resolve()), "--check-build"]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=25,
        )
        if result.returncode != 0:
            print(f"[ERROR] Executable returned non-zero exit code ({result.returncode})!")
            print("--- STDOUT ---")
            print(result.stdout)
            print("--- STDERR ---")
            print(result.stderr)
            sys.exit(1)

        print("[+] Binary executed and passed --check-build successfully!")
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines()[-5:]:
                print(f"    [APP] {line}")
    except Exception as e:
        print(f"[ERROR] Failed to run check-build test: {e}")
        sys.exit(1)

    print("=" * 70)
    print("ALL BUILD VERIFICATION CHECKS PASSED!")
    print("=" * 70)
    sys.exit(0)

if __name__ == "__main__":
    main()
