import os
import imageio_ffmpeg
import subprocess
from src.logger import get_logger

logger = get_logger("FFmpegLocator")

def get_ffmpeg_path() -> str:
    """
    Returns the absolute path to the bundled static FFmpeg binary provided by imageio-ffmpeg.
    This works across Linux, Windows, and macOS without requiring system-level installation.
    """
    exe_path = imageio_ffmpeg.get_ffmpeg_exe()
    if not exe_path or not os.path.exists(exe_path):
        err = "Bundled FFmpeg executable could not be located via imageio-ffmpeg."
        logger.error(err)
        raise RuntimeError(err)
    logger.debug(f"Resolved static FFmpeg binary path: {exe_path}")
    return exe_path

def verify_ffmpeg() -> bool:
    """
    Verifies that the FFmpeg executable can be executed on the host system.
    """
    try:
        path = get_ffmpeg_path()
        result = subprocess.run(
            [path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        valid = "ffmpeg version" in result.stdout.lower() or "ffmpeg version" in result.stderr.lower()
        if valid:
            logger.info(f"Verified static FFmpeg executable at: {path}")
        else:
            logger.warning(f"FFmpeg binary responded but did not report a valid version: {path}")
        return valid
    except Exception as e:
        logger.error(f"FFmpeg verification failed: {e}", exc_info=True)
        return False
