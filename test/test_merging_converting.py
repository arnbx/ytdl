#!/usr/bin/env python3
"""
Comprehensive Test Script to verify universal stream merging & converting workflows
across ALL video containers (webm, mp4, avi, mkv) and ALL audio codecs (m4a, opus, ogg, flac, wav):

Workflows Tested:
1. webm (VP9 video) + m4a (AAC audio) -> merging -> converting (mp4)
2. avi (raw video)  + ogg (Vorbis audio) -> merging -> converting (mp4)
3. mkv (VP9 video)  + flac (Lossless audio) -> merging -> converting (mp4)
4. webm (VP9 video) -> converting (mp4) [Video Only]
5. avi (raw video)  -> converting (mp4) [Video Only]
6. opus (WebM audio)-> converting (mp3) [Audio Only]
7. ogg (Vorbis audio)-> converting (mp3) [Audio Only]
8. wav (PCM audio)  -> converting (mp3) [Audio Only]

All logs are recorded in ./logs/ytdl.log and printed to stdout.
"""

import os
import sys
import time
import uuid
import shutil
import logging
import subprocess

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.backend.models import (
    DownloadJob,
    TaskStage,
    StreamInfo,
)
from src.backend.pipeline_manager import (
    MergeWorker,
    ConvertWorker,
    get_temp_directory,
    get_target_directory,
)
from src.backend.ffmpeg_locator import get_ffmpeg_path

# Configure logging
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, "ytdl_test_merging.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("TestUniversalMergingConverting")


class MockVideo:
    def __init__(self, title, ext_vid="webm", ext_aud="m4a"):
        self.title = title
        self.url = f"https://youtube.com/watch?v={title.replace(' ', '_')}"
        self.video_streams = [
            StreamInfo(format_id="vid", ext=ext_vid, resolution="240p", fps=15, vcodec="vp9", filesize=180000, bitrate=78, stream_type="video")
        ]
        self.audio_streams = [
            StreamInfo(format_id="aud", ext=ext_aud, resolution="audio only", fps=0, acodec="aac", filesize=300000, bitrate=128, stream_type="audio")
        ]


def create_synthetic_media(temp_dir: str, job_id: str, vid_ext: str, aud_ext: str):
    """
    Generates real test files for any container (webm, avi, mkv, mp4)
    and any audio codec (m4a, opus, ogg, flac, wav) using FFmpeg.
    """
    ffmpeg_exe = get_ffmpeg_path()
    vid_path = os.path.join(temp_dir, f"{job_id}_video.{vid_ext}") if vid_ext else None
    aud_path = os.path.join(temp_dir, f"{job_id}_audio.{aud_ext}") if aud_ext else None

    if vid_path:
        # Codec selection based on container
        vcodec = "vp9" if vid_ext in ("webm", "mkv") else "mpeg4"
        cmd_vid = [
            ffmpeg_exe, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=15",
            "-c:v", vcodec, "-b:v", "200k",
            vid_path
        ]
        logger.info(f"Generating synthetic {vid_ext.upper()} ({vcodec}) video: {' '.join(cmd_vid)}")
        res = subprocess.run(cmd_vid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0 or not os.path.exists(vid_path):
            raise RuntimeError(f"Failed to generate {vid_ext} video: {res.stderr.decode('utf-8', errors='ignore')}")

    if aud_path:
        acodec_map = {
            "m4a": "aac",
            "opus": "libopus",
            "ogg": "libvorbis",
            "flac": "flac",
            "wav": "pcm_s16le",
        }
        acodec = acodec_map.get(aud_ext, "aac")
        cmd_aud = [
            ffmpeg_exe, "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:a", acodec,
            aud_path
        ]
        logger.info(f"Generating synthetic {aud_ext.upper()} ({acodec}) audio: {' '.join(cmd_aud)}")
        res = subprocess.run(cmd_aud, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0 or not os.path.exists(aud_path):
            raise RuntimeError(f"Failed to generate {aud_ext} audio: {res.stderr.decode('utf-8', errors='ignore')}")

    return vid_path, aud_path


def verify_file_validity(path: str, expect_video: bool, expect_audio: bool):
    if not os.path.exists(path) or os.path.getsize(path) < 100:
        raise AssertionError(f"File missing or empty: {path}")

    ffmpeg_exe = get_ffmpeg_path()
    cmd = [ffmpeg_exe, "-i", path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = res.stderr.decode("utf-8", errors="ignore")

    has_video = "Video:" in output
    has_audio = "Audio:" in output

    if expect_video and not has_video:
        raise AssertionError(f"Expected video stream in {path}, but none found:\n{output}")
    if expect_audio and not has_audio:
        raise AssertionError(f"Expected audio stream in {path}, but none found:\n{output}")

    logger.info(f"VERIFIED OK ({path}): Video={has_video} (expected {expect_video}), Audio={has_audio} (expected {expect_audio})")


def run_test_workflow(wf_name: str, vid_ext: str, aud_ext: str, mode: str, expect_vid: bool, expect_aud: bool):
    logger.info(f"=== STARTING {wf_name} ===")
    temp_dir = get_temp_directory()
    job_id = f"job_{uuid.uuid4().hex[:6]}"
    
    vid_path, aud_path = create_synthetic_media(temp_dir, job_id, vid_ext, aud_ext)
    mock_vid = MockVideo(wf_name, vid_ext or "webm", aud_ext or "m4a")

    job = DownloadJob(
        job_id=job_id,
        video=mock_vid,
        selected_video_stream=mock_vid.video_streams[0] if vid_ext else None,
        selected_audio_stream=mock_vid.audio_streams[0] if aud_ext else None,
        download_mode=mode,
        playlist_name="Test_Universal_Suite"
    )
    job.temp_video_path = vid_path or ""
    job.temp_audio_path = aud_path or ""

    if mode == "video_audio":
        merger = MergeWorker(job, lambda *args, **kwargs: None, lambda *args, **kwargs: None, lambda *args, **kwargs: None)
        merger.run()
        if job.stage == TaskStage.FAILED or not job.temp_merged_path:
            raise RuntimeError(f"Merging failed for {wf_name}: {job.status_msg}")
        verify_file_validity(job.temp_merged_path, expect_video=True, expect_audio=True)

    converter = ConvertWorker(job, lambda *args, **kwargs: None, lambda *args, **kwargs: None, lambda *args, **kwargs: None)
    converter.run()

    if job.stage == TaskStage.FAILED or not job.final_file_path:
        raise RuntimeError(f"Converting failed for {wf_name}: {job.status_msg}")

    verify_file_validity(job.final_file_path, expect_video=expect_vid, expect_audio=expect_aud)
    logger.info(f"--> SUCCESS: {wf_name} generated valid output -> {job.final_file_path}")
    return job.final_file_path


def main():
    logger.info("=========================================================================")
    logger.info("  YTDL -- UNIVERSAL MULTI-FORMAT MERGING & CONVERTING SUITE              ")
    logger.info("=========================================================================")

    tests = [
        ("Workflow 1: webm(VP9) + m4a(AAC) -> MP4", "webm", "m4a", "video_audio", True, True),
        ("Workflow 2: avi(MPEG4) + ogg(Vorbis) -> MP4", "avi", "ogg", "video_audio", True, True),
        ("Workflow 3: mkv(VP9) + flac(Lossless) -> MP4", "mkv", "flac", "video_audio", True, True),
        ("Workflow 4: webm(VP9) -> MP4 [Video Only]", "webm", None, "video_only", True, False),
        ("Workflow 5: avi(MPEG4) -> MP4 [Video Only]", "avi", None, "video_only", True, False),
        ("Workflow 6: opus(WebM audio) -> MP3", None, "opus", "audio_only", False, True),
        ("Workflow 7: ogg(Vorbis audio) -> MP3", None, "ogg", "audio_only", False, True),
        ("Workflow 8: wav(PCM audio) -> MP3", None, "wav", "audio_only", False, True),
    ]

    results = []
    try:
        for wf_name, vid_ext, aud_ext, mode, exp_v, exp_a in tests:
            out_path = run_test_workflow(wf_name, vid_ext, aud_ext, mode, exp_v, exp_a)
            results.append((wf_name, out_path))

        logger.info("=========================================================================")
        logger.info("                  ALL 8 UNIVERSAL WORKFLOWS PASSED 100%!                 ")
        for wf_name, out_path in results:
            logger.info(f"  [{wf_name}] -> PASSED: {out_path}")
        logger.info("=========================================================================")
        sys.exit(0)
    except Exception as e:
        logger.error(f"TEST SUITE FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
