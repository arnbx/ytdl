import unittest

class TestQueueAggregate(unittest.TestCase):
    def compute_batch_average(self, jobs: list) -> int:
        if not jobs:
            return 0
        total_progress_sum = 0
        for job in jobs:
            stage = job.get("stage", "")
            status_msg = job.get("status_msg", "")
            p = 0
            if stage in ("Video Stream Download", "VIDEO_DOWNLOAD"):
                p = job.get("video_progress", 0) * 40
            elif stage in ("Audio Stream Download", "AUDIO_DOWNLOAD"):
                p = 40 + job.get("audio_progress", 0) * 40
            elif stage in ("Merging", "MERGING"):
                p = 80 + job.get("merge_progress", 0) * 10
            elif stage in ("Converting", "CONVERTING"):
                p = 90 + job.get("convert_progress", 0) * 10
            elif stage in ("Completed", "COMPLETED") or status_msg == "Completed":
                p = 100
            total_progress_sum += p
        return round(total_progress_sum / len(jobs))

    def test_all_completed(self):
        jobs = [
            {"stage": "Completed"},
            {"stage": "COMPLETED"},
            {"stage": "Completed"}
        ]
        self.assertEqual(self.compute_batch_average(jobs), 100)

    def test_partial_progress(self):
        jobs = [
            {"stage": "Completed"}, # 100
            {"stage": "VIDEO_DOWNLOAD", "video_progress": 0.5} # 20
        ]
        self.assertEqual(self.compute_batch_average(jobs), 60)

if __name__ == "__main__":
    unittest.main()
