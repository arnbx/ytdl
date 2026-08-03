"""
Backward-compatible wrapper for YTDL pipeline manager.
Re-exports from modular src.backend.pipeline package.
"""
from src.backend.pipeline import (
    get_target_directory,
    get_temp_directory,
    cleanup_temp_build_directory,
    PipelineManager,
    VideoDownloadWorker,
    AudioDownloadWorker,
    MergeWorker,
    ConvertWorker,
    run_ffmpeg_with_progress,
)

__all__ = [
    "get_target_directory",
    "get_temp_directory",
    "cleanup_temp_build_directory",
    "PipelineManager",
    "VideoDownloadWorker",
    "AudioDownloadWorker",
    "MergeWorker",
    "ConvertWorker",
    "run_ffmpeg_with_progress",
]
