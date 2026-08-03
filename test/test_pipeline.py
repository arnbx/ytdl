import os
import sys

# Ensure project root is in sys.path when running script directly from ./test
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.backend.ffmpeg_locator import get_ffmpeg_path, verify_ffmpeg
from src.backend.models import VideoMetadata, StreamInfo
from src.backend.extractor import group_playlist_videos, get_available_resolutions, get_available_audio_bitrates
from src.backend.pipeline_manager import get_target_directory
from src.logger import get_logger

logger = get_logger("TestSuite")

def test_ffmpeg_locator():
    print("[TEST] 1. Testing static FFmpeg locator...")
    logger.info("Running automated test: test_ffmpeg_locator")
    path = get_ffmpeg_path()
    assert os.path.exists(path), f"FFmpeg path does not exist: {path}"
    print(f"       -> PASS: Located valid static FFmpeg at: {path}")

def test_sorting_and_grouping():
    print("[TEST] 2. Testing stream quality sorting & playlist grouping...")
    logger.info("Running automated test: test_sorting_and_grouping")
    v1 = StreamInfo("v1", "mp4", "4K (2160p)", 60, "avc1", "aac", 1000, 5000, 2160000, "video")
    v2 = StreamInfo("v2", "mp4", "FHD (1080p)", 60, "avc1", "aac", 500, 2500, 1080000, "video")
    a1 = StreamInfo("a1", "m4a", "320 kbps", 0, "none", "aac", 50, 320, 320, "audio")

    vm1 = VideoMetadata(
        url="http://test1",
        title="Video 1",
        duration=120,
        thumbnail_url="",
        video_streams=[v1, v2],
        audio_streams=[a1],
        best_video=v1,
        best_audio=a1
    )
    vm2 = VideoMetadata(
        url="http://test2",
        title="Video 2",
        duration=180,
        thumbnail_url="",
        video_streams=[v2],
        audio_streams=[a1],
        best_video=v2,
        best_audio=a1
    )

    avail_res = get_available_resolutions([vm1, vm2])
    avail_audio = get_available_audio_bitrates([vm1, vm2])
    assert avail_res == ["(Best Available)", "4K (2160p)", "FHD (1080p)"], f"Unexpected avail_res: {avail_res}"
    assert "(Best Available)" in avail_audio
    print(f"       -> PASS: get_available_resolutions returned only present resolutions + (Best Available)")
    print(f"       -> PASS: get_available_audio_bitrates returned: {avail_audio}")

    groups_best = group_playlist_videos([vm1, vm2], "(Best Available)", -1.0, mode="video_audio")
    assert len(groups_best) == 1, f"Expected 1 batch group for Best Available, got {len(groups_best)}"
    assert len(groups_best[0].videos) == 2, f"Expected 2 videos in Best Available group, got {len(groups_best[0].videos)}"
    assert "All Videos - Best Available" in groups_best[0].group_name
    print(f"       -> PASS: Unified batch group for Best Available '{groups_best[0].group_name}' has {len(groups_best[0].videos)} video(s)")

    groups_4k = group_playlist_videos([vm1, vm2], "4K (2160p)", 320.0, mode="video_audio")
    assert len(groups_4k) == 2, f"Expected 2 groups for 4K (matching + fallback), got {len(groups_4k)}"
    assert len(groups_4k[0].videos) == 1 and "4K (2160p) Available" in groups_4k[0].group_name
    assert len(groups_4k[1].videos) == 1 and "Fallback to Best Available" in groups_4k[1].group_name
    print(f"       -> PASS: Split groups for 4K selection: '{groups_4k[0].group_name}' and '{groups_4k[1].group_name}'")

    groups_vo = group_playlist_videos([vm1, vm2], "4K (2160p)", -1, mode="video_only")
    assert "Video Only" in groups_vo[0].group_name
    print(f"       -> PASS: Mode 'video_only' grouping works: {groups_vo[0].group_name}")

def test_target_directories():
    print("[TEST] 3. Testing strict ./downloads/ target directories...")
    logger.info("Running automated test: test_target_directories")
    std_dir = get_target_directory(None)
    assert std_dir.endswith("downloads"), f"Expected base downloads folder, got {std_dir}"
    assert os.path.exists(std_dir)

    pl_dir = get_target_directory("My Test Playlist")
    assert "My Test Playlist" in pl_dir
    assert os.path.exists(pl_dir)
    print(f"       -> PASS: Standard folder: {std_dir}")
    print(f"       -> PASS: Playlist folder: {pl_dir}")

def test_job_progress_serialization():
    print("[TEST] 4. Testing DownloadJob progress fields and state serialization...")
    logger.info("Running automated test: test_job_progress_serialization")
    from src.backend.models import DownloadJob, TaskStage
    import src.backend.state as state
    job = DownloadJob(
        job_id="test-job-1",
        url="http://test",
        video=None,
        stage=TaskStage.VIDEO_DOWNLOAD,
        video_progress=0.45,
        video_speed="5.2 MB/s",
        video_eta="00:10"
    )
    d = state.job_to_dict(job)
    assert d["video_progress"] == 0.45, f"Expected 0.45, got {d['video_progress']}"
    assert d["video_speed"] == "5.2 MB/s", f"Expected '5.2 MB/s', got {d['video_speed']}"
    assert d["stage"] == "VIDEO_DOWNLOAD", f"Expected 'VIDEO_DOWNLOAD', got {d['stage']}"
    print("       -> PASS: DownloadJob progress fields serialized correctly in job_to_dict.")

def main():
    logger.info("--- Starting YTDL Verification Suite ---")
    try:
        test_ffmpeg_locator()
        test_sorting_and_grouping()
        test_target_directories()
        test_job_progress_serialization()
        logger.info("--- All Verification Suite Tests Passed Successfully ---")
        print("[ALL TESTS PASSED SUCCESSFULLY!]")
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        print(f"[TEST FAILED] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
