import threading
from typing import List, Optional, Dict, Callable

from src.backend.models import DownloadJob
from .temp_utils import cleanup_temp_build_directory
from .workers_download import VideoDownloadWorker, AudioDownloadWorker
from .workers_process import MergeWorker, ConvertWorker
from src.logger import get_logger

logger = get_logger("PipelineManager")


class PipelineManager:
    """
    4-Stage Concurrent Multitasking Pipeline Manager (Pure Python threading):
    Ensures at most 1 task is running per stage, while different stages run simultaneously.
    """
    def __init__(
        self,
        on_stage_progress: Optional[Callable[[str, str, float, str, str], None]] = None,
        on_job_status: Optional[Callable[[str, str, str], None]] = None
    ):
        self.on_stage_progress_cb = on_stage_progress or (lambda *args: None)
        self.on_job_status_cb = on_job_status or (lambda *args: None)

        self.lock = threading.Lock()
        self.jobs: Dict[str, DownloadJob] = {}
        self.video_queue: List[str] = []
        self.audio_queue: List[str] = []
        self.merge_queue: List[str] = []
        self.convert_queue: List[str] = []

        self.active_video_job: Optional[str] = None
        self.active_audio_job: Optional[str] = None
        self.active_merge_job: Optional[str] = None
        self.active_convert_job: Optional[str] = None

    def add_job(self, job: DownloadJob):
        with self.lock:
            self.jobs[job.job_id] = job
            mode = job.download_mode
            if mode == "video_audio":
                self.video_queue.append(job.job_id)
                self.audio_queue.append(job.job_id)
            elif mode == "video_only":
                self.video_queue.append(job.job_id)
            elif mode == "audio_only":
                self.audio_queue.append(job.job_id)
            logger.info(f"Queued job [{job.job_id}] (mode: {mode}) for video '{job.video.title if job.video else 'Unknown'}'")
        try:
            self.on_job_status_cb(job.job_id, job.stage, "Queued")
        except Exception as e:
            logger.debug(f"Error dispatching initial job status callback: {e}")
        self._schedule()

    def _schedule(self):
        with self.lock:
            # 1. Schedule Video
            if not self.active_video_job and self.video_queue:
                jid = self.video_queue.pop(0)
                self.active_video_job = jid
                job = self.jobs[jid]
                w = VideoDownloadWorker(
                    job,
                    self.on_stage_progress_cb,
                    self.on_job_status_cb,
                    self._on_video_completed
                )
                w.start()

            # 2. Schedule Audio
            if not self.active_audio_job and self.audio_queue:
                jid = self.audio_queue.pop(0)
                self.active_audio_job = jid
                job = self.jobs[jid]
                w = AudioDownloadWorker(
                    job,
                    self.on_stage_progress_cb,
                    self.on_job_status_cb,
                    self._on_audio_completed
                )
                w.start()

            # 3. Schedule Merging
            if not self.active_merge_job and self.merge_queue:
                jid = self.merge_queue.pop(0)
                self.active_merge_job = jid
                job = self.jobs[jid]
                w = MergeWorker(
                    job,
                    self.on_stage_progress_cb,
                    self.on_job_status_cb,
                    self._on_merge_completed
                )
                w.start()

            # 4. Schedule Converting
            if not self.active_convert_job and self.convert_queue:
                jid = self.convert_queue.pop(0)
                self.active_convert_job = jid
                job = self.jobs[jid]
                w = ConvertWorker(
                    job,
                    self.on_stage_progress_cb,
                    self.on_job_status_cb,
                    self._on_convert_completed
                )
                w.start()

    def _cleanup_temp_if_idle(self):
        if not any([
            self.active_video_job, self.active_audio_job,
            self.active_merge_job, self.active_convert_job,
            self.video_queue, self.audio_queue,
            self.merge_queue, self.convert_queue
        ]):
            cleanup_temp_build_directory()

    def _on_video_completed(self, job: DownloadJob, success: bool):
        with self.lock:
            self.active_video_job = None
            if success:
                if job.download_mode == "video_audio":
                    if job.temp_video_path and job.temp_audio_path and job.job_id not in self.merge_queue:
                        self.merge_queue.append(job.job_id)
                elif job.download_mode == "video_only":
                    if job.job_id not in self.convert_queue:
                        self.convert_queue.append(job.job_id)
            self._cleanup_temp_if_idle()
        self._schedule()

    def _on_audio_completed(self, job: DownloadJob, success: bool):
        with self.lock:
            self.active_audio_job = None
            if success:
                if job.download_mode == "video_audio":
                    if job.temp_video_path and job.temp_audio_path and job.job_id not in self.merge_queue:
                        self.merge_queue.append(job.job_id)
                elif job.download_mode == "audio_only":
                    if job.job_id not in self.convert_queue:
                        self.convert_queue.append(job.job_id)
            self._cleanup_temp_if_idle()
        self._schedule()

    def _on_merge_completed(self, job: DownloadJob, success: bool):
        with self.lock:
            self.active_merge_job = None
            if success:
                self.convert_queue.append(job.job_id)
            self._cleanup_temp_if_idle()
        self._schedule()

    def _on_convert_completed(self, job: DownloadJob, success: bool):
        with self.lock:
            self.active_convert_job = None
            self._cleanup_temp_if_idle()
        self._schedule()
