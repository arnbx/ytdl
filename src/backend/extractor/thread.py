import threading
from typing import List, Any, Optional, Callable
import yt_dlp

from src.backend.models import VideoMetadata
from src.backend.ffmpeg_locator import get_ffmpeg_path
from .stream_parser import extract_video_metadata
from src.logger import get_logger

logger = get_logger("ExtractorThread")

def _build_flat_video_metadata(entry: Any, idx: int) -> VideoMetadata:
    title = entry.get("title", f"Video {idx + 1}")
    vid_id = entry.get("id", "")
    url = entry.get("url") or entry.get("webpage_url") or (f"https://www.youtube.com/watch?v={vid_id}" if vid_id else "")
    duration = entry.get("duration", 0)
    thumbs = entry.get("thumbnails", [])
    thumb_url = ""
    if thumbs and isinstance(thumbs, list):
        thumb_url = thumbs[-1].get("url", "")
    elif entry.get("thumbnail"):
        thumb_url = entry.get("thumbnail", "")

    return VideoMetadata(
        url=url,
        title=title,
        duration=int(duration) if duration else 0,
        thumbnail_url=thumb_url,
        video_streams=[],
        audio_streams=[],
        best_video=None,
        best_audio=None
    )

class ExtractorThread(threading.Thread):
    def __init__(
        self,
        url: str,
        on_success: Callable[[Any, bool, str], None],
        on_error: Callable[[str], None],
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        noplaylist: bool = True
    ):
        super().__init__(daemon=True)
        self.url = url.strip()
        self.on_success = on_success
        self.on_error = on_error
        self.on_progress = on_progress
        self.noplaylist = noplaylist

    def run(self):
        logger.info(f"Starting URL extraction for: {self.url}")
        if self.on_progress:
            self.on_progress("Analyzing stream URL...", 0, 0)
        is_single_video = "/playlist" not in self.url
        try:
            flat_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False if is_single_video else 'in_playlist',
                'noplaylist': True if is_single_video else False,
                'ignoreerrors': True,
                'extractor_args': {'youtube': {'player_client': ['android_vr', 'web']}},
                'ffmpeg_location': get_ffmpeg_path(),
            }
            with yt_dlp.YoutubeDL(flat_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            if not info:
                msg = "Could not retrieve stream information from the provided URL. Video may be private, deleted, or restricted."
                logger.error(msg)
                self.on_error(msg)
                return

            if "entries" in info and info.get("_type") in ("playlist", "multi_video") or "entries" in info:
                playlist_title = info.get("title", "YouTube Playlist")
                entries = [e for e in info.get("entries", []) if e is not None]
                total = len(entries)
                if self.on_progress:
                    self.on_progress(f"Found {total} videos in playlist '{playlist_title}'.", 0, total)
                
                videos: List[VideoMetadata] = []
                for idx, entry in enumerate(entries):
                    vm = _build_flat_video_metadata(entry, idx)
                    videos.append(vm)

                if not videos:
                    msg = f"No downloadable videos found in playlist '{playlist_title}'."
                    logger.error(msg)
                    self.on_error(msg)
                    return

                logger.info(f"Successfully scanned flat playlist '{playlist_title}' with {len(videos)} videos.")
                self.on_success(videos, True, playlist_title)
            else:
                if self.on_progress:
                    self.on_progress("Stream analyzed!", 1, 1)
                vm = extract_video_metadata(info)
                if not vm.best_video and not vm.best_audio:
                    msg = f"Video '{vm.title}' has no downloadable video or audio streams (possibly private or restricted)."
                    logger.error(msg)
                    self.on_error(msg)
                    return
                logger.info(f"Successfully extracted single video: '{vm.title}' ({vm.formatted_duration})")
                self.on_success([vm], False, vm.title)
        except Exception as e:
            logger.error(f"URL extraction failed for '{self.url}': {e}", exc_info=True)
            self.on_error(str(e))
