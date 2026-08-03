from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid

class TaskStage(Enum):
    WAITING = "WAITING"
    VIDEO_DOWNLOAD = "VIDEO_DOWNLOAD"
    AUDIO_DOWNLOAD = "AUDIO_DOWNLOAD"
    MERGING = "MERGING"
    CONVERTING = "CONVERTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class StreamInfo:
    format_id: str
    ext: str
    resolution: str
    fps: Optional[float] = 0.0
    vcodec: str = "none"
    acodec: str = "none"
    filesize: Optional[int] = 0
    bitrate: Optional[float] = 0.0
    quality_score: float = 0.0
    stream_type: str = "video"  # "video" or "audio"

    @property
    def display_label(self) -> str:
        size_str = f"{self.filesize / (1024*1024):.1f} MB" if self.filesize and self.filesize > 0 else "Unknown size"
        if self.stream_type == "video":
            fps_str = f" @ {int(self.fps)}fps" if self.fps and self.fps > 0 else ""
            codec_short = self.vcodec.split(".")[0] if self.vcodec else ""
            return f"{self.resolution}{fps_str} - [{self.ext.upper()}] ({size_str}) [{codec_short}]"
        else:
            abr_str = f"{int(self.bitrate)} kbps" if self.bitrate and self.bitrate > 0 else "Audio"
            codec_short = self.acodec.split(".")[0] if self.acodec else ""
            return f"{abr_str} - [{self.ext.upper()}] ({size_str}) [{codec_short}]"

@dataclass
class VideoMetadata:
    url: str
    title: str
    duration: int = 0
    thumbnail_url: str = ""
    video_streams: List[StreamInfo] = field(default_factory=list)
    audio_streams: List[StreamInfo] = field(default_factory=list)
    best_video: Optional[StreamInfo] = None
    best_audio: Optional[StreamInfo] = None

    @property
    def formatted_duration(self) -> str:
        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

@dataclass
class PlaylistGroup:
    group_name: str
    quality_tier: str
    videos: List[VideoMetadata] = field(default_factory=list)
    selected_video_format_id: str = ""
    selected_audio_format_id: str = ""

@dataclass
class DownloadJob:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    video: Optional[VideoMetadata] = None
    playlist_name: Optional[str] = None
    selected_video_stream: Optional[StreamInfo] = None
    selected_audio_stream: Optional[StreamInfo] = None
    download_mode: str = "video_audio"  # "video_audio", "video_only", "audio_only"
    stage: TaskStage = TaskStage.WAITING
    
    # Live progress metrics for each pipeline stage
    video_progress: float = 0.0
    video_speed: str = "0 KB/s"
    video_eta: str = "--:--"
    
    audio_progress: float = 0.0
    audio_speed: str = "0 KB/s"
    audio_eta: str = "--:--"
    
    merge_progress: float = 0.0
    convert_progress: float = 0.0
    
    status_msg: str = "Waiting in queue..."
    output_filepath: str = ""
    temp_video_path: str = ""
    temp_audio_path: str = ""
    temp_merged_path: str = ""
    video_part_path: str = ""
    audio_part_path: str = ""
    error_message: str = ""
