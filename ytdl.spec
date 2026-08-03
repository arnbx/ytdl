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
a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "_tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

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
    console=False,       # No terminal window for end users
    icon=None,           # Replace with icon path e.g. "assets/icon.ico" (Win) / "assets/icon.icns" (Mac)
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
        icon=None,           # Replace with "assets/icon.icns" when available
        bundle_identifier="com.ytdl.downloader",
        info_plist={
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "YTDL",
            "CFBundleShortVersionString": "1.0.0",
        },
    )
