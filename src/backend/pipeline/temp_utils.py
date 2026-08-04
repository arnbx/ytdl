import os
import shutil
from typing import Optional
from src.logger import get_logger

logger = get_logger("PipelineTempUtils")

def get_base_downloads_dir() -> str:
    home_dir = os.path.expanduser("~")
    downloads_dir = os.path.join(home_dir, "Downloads", "ytdl")
    return os.path.abspath(downloads_dir)


def get_target_directory(playlist_name: Optional[str]) -> str:
    base_dir = get_base_downloads_dir()
    if playlist_name and playlist_name.strip():
        safe_pl = "".join(c for c in playlist_name if c.isalnum() or c in (" ", "-", "_")).strip()
        target_dir = os.path.join(base_dir, safe_pl or "Playlist")
    else:
        target_dir = base_dir
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


def get_temp_directory() -> str:
    temp_dir = os.path.join(get_base_downloads_dir(), ".temp_build")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def cleanup_temp_build_directory():
    """
    Removes the temporary build directories (.temp_build and .tmp_build) and all of their contents
    once video downloading/conversion completes successfully.
    """
    base_dir = get_base_downloads_dir()
    for name in (".temp_build", ".tmp_build"):
        path = os.path.join(base_dir, name)
        if os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=True)
                logger.debug(f"Removed temporary build folder and all contents: {path}")
            except Exception as e:
                logger.warning(f"Failed to remove temp build directory {path}: {e}")
