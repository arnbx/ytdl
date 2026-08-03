import os
import threading
from typing import Optional, Callable

from src.backend.models import DownloadJob, TaskStage
from src.backend.ffmpeg_locator import get_ffmpeg_path
from .temp_utils import get_target_directory
from src.logger import get_logger

logger = get_logger("ConvertWorker")

class ConvertWorker(threading.Thread):
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
        from .workers_process import run_ffmpeg_with_progress
        self.job.stage = TaskStage.CONVERTING
        self.job.status_msg = "Finalizing File..."
        self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
        logger.info(f"[{self.job.job_id}] Started Stage 4 (Converting/Finalizing)")

        title = self.job.video.title if self.job.video else "Video"
        self.on_progress("CONVERTING", title, 30.0, "Converting", "N/A")

        target_dir = get_target_directory(self.job.playlist_name)
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_", ".")).strip() or "output"

        mode = self.job.download_mode

        source_path = ""
        if mode == "video_audio":
            source_path = self.job.temp_merged_path
        elif mode == "video_only":
            source_path = self.job.temp_video_path
        elif mode == "audio_only":
            source_path = self.job.temp_audio_path

        ext = "mp3" if mode == "audio_only" else ("mkv" if (source_path and source_path.endswith(".mkv")) else "mp4")
        final_path = os.path.join(target_dir, f"{safe_title}.{ext}")

        if not source_path or not os.path.exists(source_path):
            err = "Convert error: source file missing"
            self.job.status_msg = err
            self.job.stage = TaskStage.FAILED
            logger.error(f"[{self.job.job_id}] Stage 4 failed: {err}")
            self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
            self.on_complete(self.job, False)
            return

        counter = 1
        base_title = safe_title
        while os.path.exists(final_path) and os.path.abspath(final_path) != os.path.abspath(source_path):
            final_path = os.path.join(target_dir, f"{base_title}_{counter}.{ext}")
            counter += 1

        try:
            if mode in ("video_audio", "video_only") and source_path.endswith((".mp4", ".mkv")):
                if os.path.exists(final_path) and os.path.abspath(final_path) != os.path.abspath(source_path):
                    os.remove(final_path)
                os.rename(source_path, final_path)
            else:
                ffmpeg_exe = get_ffmpeg_path()
                success = False
                if ext == "mp3":
                    cmd_mp3 = [ffmpeg_exe, "-y", "-i", source_path, "-vn", "-c:a", "libmp3lame", "-b:a", "192k", "-id3v2_version", "3", final_path]
                    success = run_ffmpeg_with_progress(cmd_mp3, self.job, self.on_progress, self.on_status, "CONVERTING", "Converting", title, final_path)
                    if not success:
                        cmd_fallback = [ffmpeg_exe, "-y", "-i", source_path, "-vn", "-c:a", "libmp3lame", "-q:a", "2", final_path]
                        success = run_ffmpeg_with_progress(cmd_fallback, self.job, self.on_progress, self.on_status, "CONVERTING", "Converting", title, final_path)
                else:
                    cmd_copy = [ffmpeg_exe, "-y", "-i", source_path, "-c", "copy", final_path]
                    success = run_ffmpeg_with_progress(cmd_copy, self.job, self.on_progress, self.on_status, "CONVERTING", "Converting", title, final_path)
                    if not success:
                        cmd_transcode = [
                            ffmpeg_exe, "-y", "-i", source_path,
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23"
                        ]
                        if mode == "video_only":
                            cmd_transcode.append("-an")
                        else:
                            cmd_transcode.extend(["-c:a", "aac", "-b:a", "192k"])
                        cmd_transcode.append(final_path)
                        success = run_ffmpeg_with_progress(cmd_transcode, self.job, self.on_progress, self.on_status, "CONVERTING", "Transcoding", title, final_path)

                if not success or not os.path.exists(final_path):
                    raise RuntimeError("FFmpeg conversion failed after all fallback attempts.")
                if os.path.exists(source_path) and os.path.abspath(source_path) != os.path.abspath(final_path):
                    os.remove(source_path)

            self.job.output_filepath = final_path
            self.job.convert_progress = 1.0
            self.job.stage = TaskStage.COMPLETED
            self.job.status_msg = "Completed"
            logger.info(f"[{self.job.job_id}] Job Completed -> {final_path}")
            self.on_progress("CONVERTING", title, 100.0, "Completed", "00:00")
            self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
            self.on_complete(self.job, True)
        except Exception as e:
            self.job.status_msg = f"Convert error: {e}"
            self.job.stage = TaskStage.FAILED
            logger.error(f"[{self.job.job_id}] Stage 4 failed: {e}", exc_info=True)
            self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
            self.on_complete(self.job, False)
