from typing import List, Dict, Any, Optional
from dataclasses import asdict
from fastapi import WebSocket
from src.backend.models import VideoMetadata, StreamInfo, DownloadJob
from src.logger import get_logger

logger = get_logger("BackendState")

# Global in-memory state
current_videos: List[VideoMetadata] = []
current_playlist_title: str = "YouTube Video / Playlist"
active_websockets: List[WebSocket] = []
pipeline_manager = None
main_loop: Optional[Any] = None

def get_current_videos(req_app_state=None) -> List[VideoMetadata]:
    if req_app_state and hasattr(req_app_state, "current_videos") and req_app_state.current_videos:
        return req_app_state.current_videos
    return current_videos

def stream_to_dict(stream: Optional[StreamInfo]) -> Optional[Dict[str, Any]]:
    if not stream:
        return None
    d = asdict(stream)
    d["display_label"] = stream.display_label
    return d

def video_to_dict(video: VideoMetadata, idx: int = 0) -> Dict[str, Any]:
    return {
        "index": idx,
        "url": video.url,
        "title": video.title,
        "duration": video.duration,
        "formatted_duration": video.formatted_duration,
        "thumbnail_url": video.thumbnail_url,
        "video_streams": [stream_to_dict(s) for s in video.video_streams],
        "audio_streams": [stream_to_dict(s) for s in video.audio_streams],
        "best_video": stream_to_dict(video.best_video),
        "best_audio": stream_to_dict(video.best_audio)
    }

def job_to_dict(job: DownloadJob) -> Dict[str, Any]:
    title = job.video.title if job.video else "Unknown Video"
    return {
        "job_id": job.job_id,
        "title": title,
        "playlist_name": job.playlist_name,
        "download_mode": job.download_mode,
        "stage": job.stage.value,
        "video_progress": job.video_progress,
        "video_speed": job.video_speed,
        "video_eta": job.video_eta,
        "audio_progress": job.audio_progress,
        "audio_speed": job.audio_speed,
        "audio_eta": job.audio_eta,
        "merge_progress": job.merge_progress,
        "convert_progress": job.convert_progress,
        "status_msg": job.status_msg,
        "error_message": job.error_message,
        "output_filepath": job.output_filepath
    }
