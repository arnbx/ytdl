# -*- mode: python ; coding: utf-8 -*-
# YTDL — PyInstaller Build Spec
# Handles all three platforms: Linux, Windows, macOS

import sys
import os

# ─── Platform detection ──────────────────────────────────────────────────────
IS_WINDOWS = sys.platform.startswith("win")
IS_MAC     = sys.platform == "darwin"
IS_LINUX   = sys.platform.startswith("linux")

# ─── Hidden imports ───────────────────────────────────────────────────────────
# PyWebView platform backends must be explicitly declared so PyInstaller
# can collect them — they are imported dynamically at runtime.
hidden_imports = [
    "webview",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "starlette",
    "yt_dlp",
    "imageio_ffmpeg",
    "anyio",
    "anyio._backends._asyncio",
    "websockets",
    "websockets.legacy",
    "websockets.legacy.server",
]

if IS_LINUX:
    hidden_imports += ["webview.platforms.gtk"]
elif IS_WINDOWS:
    hidden_imports += [
        "webview.platforms.winforms",
        "clr",
        "System",
        "System.Windows.Forms",
    ]
elif IS_MAC:
    hidden_imports += ["webview.platforms.cocoa"]

# ─── Data files: bundle the entire web frontend ───────────────────────────────
sep = ";" if IS_WINDOWS else ":"
datas = [
    (f"src{os.sep}web", f"src{os.sep}web"),
]

# ─── Analysis ─────────────────────────────────────────────────────────────────
base_excludes = [
    "tkinter",
    "test",
    "_tkinter",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "qtpy",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "notebook",
    "IPython",
    "docutils",
    "sphinx",
    "pytest",
    "unittest",
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=base_excludes,
    noarchive=False,
)

# On Linux, exclude host system libraries (glib, gobject, gio, girepository, gtk, webkit, cairo, pango, etc.)
# from a.binaries so they load dynamically from the host OS without symbol clash errors.
if not IS_WINDOWS and not IS_MAC:
    linux_sys_prefixes = (
        "libglib-2.0",
        "libgobject-2.0",
        "libgio-2.0",
        "libgmodule-2.0",
        "libgthread-2.0",
        "libgirepository-1.0",
        "libgtk-3",
        "libgdk-3",
        "libwebkit2gtk",
        "libjavascriptcoregtk",
        "libcairo",
        "libpango",
        "libffi",
        "libwayland",
        "libX",
        "libdrm",
        "libgbm",
        "libEGL",
        "libGL",
        "libGLES",
        "libxcb",
        "libxkbcommon",
        "libdbus",
        "libfontconfig",
        "libfreetype",
    )
    a.binaries = [
        b for b in a.binaries
        if not b[0].startswith(linux_sys_prefixes) and not any(f"/{p}" in b[1] for p in linux_sys_prefixes)
    ]

pyz = PYZ(a.pure)

win_icon = "icon/icon.ico" if os.path.exists("icon/icon.ico") else None
mac_icon = "icon/icon.icns" if os.path.exists("icon/icon.icns") else None
linux_icon = "icon/icon-256.png" if os.path.exists("icon/icon-256.png") else None

if IS_WINDOWS:
    # Build single standalone executable (.exe) for Windows
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="YTDL",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,       # No terminal window for end users
        icon=win_icon,       # Uses icon/icon.ico for Windows
        version="version_info.txt" if os.path.exists("version_info.txt") else None,
    )
else:
    # Build directory bundle for Linux AppImage and macOS .app / .dmg
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="YTDL",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon=linux_icon,     # Uses icon/icon-256.png for Linux
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="YTDL",
    )

# ─── macOS .app bundle ────────────────────────────────────────────────────────
if IS_MAC:
    app = BUNDLE(
        coll,
        name="YTDL.app",
        icon=mac_icon,       # Uses icon/icon.icns for macOS .app
        bundle_identifier="dev.arnabbose.ytdl",
        info_plist={
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "Copyright © 2026 Arnab Bose. All rights reserved.",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleGetInfoString": "YTDL by Arnab Bose",
            "CFBundleName": "YTDL",
            "CFBundleDisplayName": "YTDL",
            "CFBundleIdentifier": "dev.arnabbose.ytdl",
        },
    )

