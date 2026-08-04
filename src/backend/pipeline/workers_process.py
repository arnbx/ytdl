import os
import re
import sys
import subprocess
import threading
from typing import List, Optional, Callable

from src.backend.models import DownloadJob, TaskStage
from src.backend.ffmpeg_locator import get_ffmpeg_path
from .temp_utils import get_temp_directory
from .workers_convert import ConvertWorker
from src.logger import get_logger

logger = get_logger("PipelineProcessWorkers")

export_ConvertWorker = ConvertWorker

def run_ffmpeg_with_progress(
    cmd: List[str],
    job: DownloadJob,
    on_progress_cb: Callable[[str, str, float, str, str], None],
    on_status_cb: Callable[[str, str, str], None],
    stage_name: str,
    stage_label: str,
    title: str,
    output_path: str
) -> bool:
    duration = getattr(job.video, "duration", 100.0) if job.video else 100.0
    if not duration or duration <= 0:
        duration = 100.0

    # Ensure non-interactive mode and machine-readable progress on stderr
    if len(cmd) > 0 and not any(arg == "-nostdin" for arg in cmd):
        cmd = [cmd[0], "-nostdin"] + cmd[1:]
    if len(cmd) > 0 and not any(arg == "-progress" for arg in cmd):
        cmd = [cmd[0], "-progress", "pipe:2"] + cmd[1:]

    popen_kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.PIPE,
        "universal_newlines": True,
        "bufsize": 1,
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    process = subprocess.Popen(cmd, **popen_kwargs)

    time_pattern = re.compile(r"(?:out_)?time=\s*(\d{2}):(\d{2}):(\d{2})")
    ms_pattern = re.compile(r"out_time_ms=(\d+)")
    stderr_lines = []

    if process.stderr:
        for line in process.stderr:
            stderr_lines.append(line)
            current_sec = None
            match_time = time_pattern.search(line)
            if match_time:
                h, m, s = map(int, match_time.groups())
                current_sec = float(h * 3600 + m * 60 + s)
            else:
                match_ms = ms_pattern.search(line)
                if match_ms:
                    current_sec = float(match_ms.group(1)) / 1000000.0

            if current_sec is not None:
                percent = min(99.0, max(5.0, (current_sec / duration) * 100.0))
                if stage_name == "MERGING":
                    job.merge_progress = percent / 100.0
                elif stage_name == "CONVERTING":
                    job.convert_progress = percent / 100.0
                on_progress_cb(stage_name, title, percent, f"{stage_label} ({int(percent)}%)", "--:--")
                on_status_cb(job.job_id, f"{stage_label} ({int(percent)}%)...", job.stage.value)

    process.wait()
    success = (process.returncode == 0) and os.path.exists(output_path)
    if not success:
        logger.debug(f"[{job.job_id}] FFmpeg command failed: {' '.join(cmd)}\nStderr: {''.join(stderr_lines[-10:])}")
    return success


class MergeWorker(threading.Thread):
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
        self.job.stage = TaskStage.MERGING
        self.job.status_msg = "Merging Video and Audio..."
        self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
        logger.info(f"[{self.job.job_id}] Started Stage 3 (Merging): Muxing video and audio streams")

        title = self.job.video.title if self.job.video else "Unknown Video"
        self.on_progress("MERGING", title, 10.0, "Muxing", "N/A")

        target_dir = get_temp_directory()
        merged_ext = ".mkv" if (self.job.temp_video_path and self.job.temp_video_path.endswith((".webm", ".mkv"))) else ".mp4"
        merged_path = os.path.join(target_dir, f"{self.job.job_id}_merged{merged_ext}")

        if not self.job.temp_video_path or not os.path.exists(self.job.temp_video_path):
            err = f"Merge failed: video temp file missing ({self.job.temp_video_path})"
            self.job.status_msg = err
            self.job.stage = TaskStage.FAILED
            logger.error(f"[{self.job.job_id}] Stage 3 (Merging) failed: {err}")
            self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
            self.on_complete(self.job, False)
            return

        if not self.job.temp_audio_path or not os.path.exists(self.job.temp_audio_path):
            err = f"Merge failed: audio temp file missing ({self.job.temp_audio_path})"
            self.job.status_msg = err
            self.job.stage = TaskStage.FAILED
            logger.error(f"[{self.job.job_id}] Stage 3 (Merging) failed: {err}")
            self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
            self.on_complete(self.job, False)
            return

        try:
            ffmpeg_exe = get_ffmpeg_path()
            success = False

            cmd_copy = [
                ffmpeg_exe, "-y",
                "-i", self.job.temp_video_path,
                "-i", self.job.temp_audio_path,
                "-c:v", "copy",
                "-c:a", "copy",
                merged_path
            ]
            success = run_ffmpeg_with_progress(cmd_copy, self.job, self.on_progress, self.on_status, "MERGING", "Muxing", title, merged_path)
            if not success:
                cmd_aac = [
                    ffmpeg_exe, "-y",
                    "-i", self.job.temp_video_path,
                    "-i", self.job.temp_audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    merged_path
                ]
                success = run_ffmpeg_with_progress(cmd_aac, self.job, self.on_progress, self.on_status, "MERGING", "Muxing", title, merged_path)
            if not success:
                cmd_transcode = [
                    ffmpeg_exe, "-y",
                    "-i", self.job.temp_video_path,
                    "-i", self.job.temp_audio_path,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "192k",
                    merged_path
                ]
                success = run_ffmpeg_with_progress(cmd_transcode, self.job, self.on_progress, self.on_status, "MERGING", "Transcoding", title, merged_path)

            if success:
                self.job.temp_merged_path = merged_path
                self.job.merge_progress = 1.0
                self.on_progress("MERGING", title, 100.0, "Done", "00:00")
                self.job.status_msg = "Merged successfully"
                logger.info(f"[{self.job.job_id}] Completed Stage 3 -> {merged_path}")
                self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
                self._cleanup_files([self.job.temp_video_path, self.job.temp_audio_path])
                self.on_complete(self.job, True)
            else:
                raise RuntimeError("FFmpeg merging failed after all fallback attempts.")
        except Exception as e:
            self.job.status_msg = f"Merge error: {e}"
            self.job.stage = TaskStage.FAILED
            logger.error(f"[{self.job.job_id}] Stage 3 failed: {e}", exc_info=True)
            self.on_status(self.job.job_id, self.job.status_msg, self.job.stage.value)
            self.on_complete(self.job, False)

    def _cleanup_files(self, paths: List[Optional[str]]):
        for p in paths:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e:
                    logger.warning(f"Could not delete temp file '{p}': {e}")
