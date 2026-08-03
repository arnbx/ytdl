import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.backend.web_api import app
from src.backend.models import VideoMetadata, StreamInfo

class TestWebAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Mock current videos in app state
        s_4k = StreamInfo(
            format_id="1", ext="mp4", resolution="4K (2160p)", fps=60,
            vcodec="avc", acodec="aac", filesize=1000000, bitrate=320, quality_score=100.0, stream_type="video"
        )
        s_1080 = StreamInfo(
            format_id="2", ext="mp4", resolution="1080p", fps=30,
            vcodec="avc", acodec="aac", filesize=500000, bitrate=128, quality_score=80.0, stream_type="video"
        )
        
        self.v1 = VideoMetadata(
            title="Video 4K", duration=100,
            thumbnail_url="http://thumb", url="http://yt/1",
            video_streams=[s_4k, s_1080], audio_streams=[s_4k],
            best_video=s_4k, best_audio=s_4k
        )
        self.v2 = VideoMetadata(
            title="Video 1080p Only", duration=200,
            thumbnail_url="http://thumb", url="http://yt/2",
            video_streams=[s_1080], audio_streams=[s_1080],
            best_video=s_1080, best_audio=s_1080
        )
        app.state.current_videos = [self.v1, self.v2]

    def test_get_queue(self):
        resp = self.client.get("/api/queue")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("jobs", data)

    def test_group_playlist_best_available_single_group(self):
        resp = self.client.post("/api/group_playlist", json={
            "target_video_res": "(Best Available)",
            "target_audio_bitrate": -1.0,
            "mode": "video_audio"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["groups"]), 1)
        self.assertEqual(data["groups"][0]["group_name"], "All Videos - Best Available Video & Audio (.MP4) (2 videos)")

    def test_group_playlist_specific_resolution_two_groups(self):
        resp = self.client.post("/api/group_playlist", json={
            "target_video_res": "4K (2160p)",
            "target_audio_bitrate": -1.0,
            "mode": "video_audio"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["groups"]), 2)
        self.assertIn("4K (2160p) Available", data["groups"][0]["group_name"])
        self.assertIn("Fallback to Best Available", data["groups"][1]["group_name"])

    def test_group_playlist_multi_tier(self):
        resp = self.client.post("/api/group_playlist", json={
            "tiers": [
                {"target_res": "4K (2160p)", "target_abr": "Best Available"},
                {"target_res": "1440p", "target_abr": "Best Available"}
            ],
            "mode": "video_audio"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["groups"]), 2)
        self.assertIn("Tier 1", data["groups"][0]["group_name"])
        self.assertIn("Fallback Group", data["groups"][1]["group_name"])

    def test_open_folder(self):
        resp = self.client.post("/api/open_folder")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])

    def test_websocket_progress(self):
        with self.client.websocket_connect("/ws/progress") as websocket:
            data = websocket.receive_json()
            self.assertEqual(data["event"], "progress_update")
            self.assertIn("jobs", data)

if __name__ == "__main__":
    unittest.main()
