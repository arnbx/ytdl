import os
import time
import threading
from typing import Callable
import yt_dlp

from src.backend.models import DownloadJob, TaskStage
from src.backend.ffmpeg_locator import get_ffmpeg_path
from .temp_utils import get_temp_directory
from src.logger import get_logger

logger = get_logger("PipelineDownloadWorkers")


class VideoDownloadWorker(threading.Thread):
    def __init__(
        self,
        job: DownloadJob,
        on_progress: Callable[[str, str, float, str, str], None],
        on_status: Callable[[str, str, str], None],
        on_complete: Callable[[DownloadJob, bool], None]
    ):
        super().__init__(daemon=True)
        self.job = job
        self.on_progress = on_progress
        self.on_status = on_status
        self.on_complete = on_complete

    def run(self):
        self.job.stage = TaskStage.VIDEO_DOWNLOAD
        self.job.status_msg = "Downloading Video Stream..."
        self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
        logger.info(f"[{self.job.job_id}] Started Stage 1 (Video Download): {self.job.video.title if self.job.video else 'Unknown'}")

        target_dir = get_temp_directory()
        out_template = os.path.join(target_dir, f"{self.job.job_id}_video.%(ext)s")
        title = self.job.video.title if self.job.video else "Unknown Video"

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                percent = (downloaded / total * 100.0) if total > 0 else 0.0
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                self.job.video_progress = min(1.0, max(0.0, percent / 100.0))
                self.job.video_speed = str(speed)
                self.job.video_eta = str(eta)
                self.on_progress("VIDEO_DOWNLOAD", title, percent, speed, eta)
            elif d['status'] == 'finished':
                self.job.temp_video_path = d.get('filename')
                self.job.video_progress = 1.0
                self.job.video_speed = "Done"
                self.job.video_eta = "00:00"
                self.on_progress("VIDEO_DOWNLOAD", title, 100.0, "0 KB/s", "00:00")
                logger.debug(f"[{self.job.job_id}] Video stream temp file saved: {self.job.temp_video_path}")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': out_template,
            'format': self.job.selected_video_stream.format_id if self.job.selected_video_stream else 'bestvideo',
            'progress_hooks': [progress_hook],
            'retries': 10,
            'fragment_retries': 10,
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android_vr', 'web']}},
            'ffmpeg_location': get_ffmpeg_path(),
        }

        max_attempts = 10
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.job.video.url])

                prefix = os.path.join(target_dir, f"{self.job.job_id}_video.")
                found_file = None
                for fn in os.listdir(target_dir):
                    full_path = os.path.join(target_dir, fn)
                    if full_path.startswith(prefix) and not fn.endswith(".part") and not fn.endswith(".ytdl"):
                        found_file = full_path
                        break

                if not found_file or not os.path.exists(found_file):
                    raise RuntimeError("Video download finished but temp file was not found on disk.")

                self.job.temp_video_path = found_file
                self.job.status_msg = "Video stream downloaded"
                logger.info(f"[{self.job.job_id}] Completed Stage 1 (Video Download) on attempt {attempt}")
                self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
                self.on_complete(self.job, True)
                return
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.job.job_id}] Stage 1 attempt {attempt}/{max_attempts} failed: {e}")
                if attempt < max_attempts:
                    self.job.status_msg = f"Retrying video ({attempt+1}/{max_attempts})..."
                    self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
                    time.sleep(2)

        self.job.status_msg = f"Video error after {max_attempts} attempts: {last_error}"
        self.job.stage = TaskStage.FAILED
        logger.error(f"[{self.job.job_id}] Stage 1 failed after {max_attempts} attempts: {last_error}", exc_info=True)
        self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
        self.on_complete(self.job, False)


class AudioDownloadWorker(threading.Thread):
    def __init__(
        self,
        job: DownloadJob,
        on_progress: Callable[[str, str, float, str, str], None],
        on_status: Callable[[str, str, str], None],
        on_complete: Callable[[DownloadJob, bool], None]
    ):
        super().__init__(daemon=True)
        self.job = job
        self.on_progress = on_progress
        self.on_status = on_status
        self.on_complete = on_complete

    def run(self):
        self.job.stage = TaskStage.AUDIO_DOWNLOAD
        self.job.status_msg = "Downloading Audio Stream..."
        self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
        logger.info(f"[{self.job.job_id}] Started Stage 2 (Audio Download): {self.job.video.title if self.job.video else 'Unknown'}")

        target_dir = get_temp_directory()
        out_template = os.path.join(target_dir, f"{self.job.job_id}_audio.%(ext)s")
        title = self.job.video.title if self.job.video else "Unknown Audio"

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                percent = (downloaded / total * 100.0) if total > 0 else 0.0
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                self.job.audio_progress = min(1.0, max(0.0, percent / 100.0))
                self.job.audio_speed = str(speed)
                self.job.audio_eta = str(eta)
                self.on_progress("AUDIO_DOWNLOAD", title, percent, speed, eta)
            elif d['status'] == 'finished':
                self.job.temp_audio_path = d.get('filename')
                self.job.audio_progress = 1.0
                self.job.audio_speed = "Done"
                self.job.audio_eta = "00:00"
                self.on_progress("AUDIO_DOWNLOAD", title, 100.0, "0 KB/s", "00:00")
                logger.debug(f"[{self.job.job_id}] Audio stream temp file saved: {self.job.temp_audio_path}")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': out_template,
            'format': self.job.selected_audio_stream.format_id if self.job.selected_audio_stream else 'bestaudio',
            'progress_hooks': [progress_hook],
            'retries': 10,
            'fragment_retries': 10,
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android_vr', 'web']}},
            'ffmpeg_location': get_ffmpeg_path(),
        }

        max_attempts = 10
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.job.video.url])

                prefix = os.path.join(target_dir, f"{self.job.job_id}_audio.")
                found_file = None
                for fn in os.listdir(target_dir):
                    full_path = os.path.join(target_dir, fn)
                    if full_path.startswith(prefix) and not fn.endswith(".part") and not fn.endswith(".ytdl"):
                        found_file = full_path
                        break

                if not found_file or not os.path.exists(found_file):
                    raise RuntimeError("Audio download finished but temp file was not found on disk.")

                self.job.temp_audio_path = found_file
                self.job.status_msg = "Audio stream downloaded"
                logger.info(f"[{self.job.job_id}] Completed Stage 2 (Audio Download) on attempt {attempt}")
                self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
                self.on_complete(self.job, True)
                return
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.job.job_id}] Stage 2 attempt {attempt}/{max_attempts} failed: {e}")
                if attempt < max_attempts:
                    self.job.status_msg = f"Retrying audio ({attempt+1}/{max_attempts})..."
                    self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
                    time.sleep(2)

        self.job.status_msg = f"Audio error after {max_attempts} attempts: {last_error}"
        self.job.stage = TaskStage.FAILED
        logger.error(f"[{self.job.job_id}] Stage 2 failed after {max_attempts} attempts: {last_error}", exc_info=True)
        self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
        self.on_complete(self.job, False)
