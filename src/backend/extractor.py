"""
Backward-compatible wrapper for YTDL extractor module.
Re-exports from modular src.backend.extractor package.
"""
from src.backend.extractor import (
    parse_format_item,
    extract_video_metadata,
    get_available_resolutions,
    get_available_audio_bitrates,
    group_playlist_videos,
    ExtractorThread,
)

__all__ = [
    "parse_format_item",
    "extract_video_metadata",
    "get_available_resolutions",
    "get_available_audio_bitrates",
    "group_playlist_videos",
    "ExtractorThread",
]
