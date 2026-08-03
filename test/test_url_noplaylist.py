import unittest

class TestUrlNoPlaylist(unittest.TestCase):
    def check_is_single_video(self, url: str) -> bool:
        return "/playlist" not in url

    def test_single_video_with_list_param(self):
        url = "https://www.youtube.com/watch?v=IhU7SuNKZQY&list=PLFOU_72y-qa8&index=1&t=2s"
        self.assertTrue(self.check_is_single_video(url))

    def test_short_youtu_be_with_si_param(self):
        url = "https://youtu.be/IhU7SuNKZQY?si=kG_nZT_p4i_jPAt6"
        self.assertTrue(self.check_is_single_video(url))

    def test_pure_playlist_url(self):
        url = "https://www.youtube.com/playlist?list=PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt"
        self.assertFalse(self.check_is_single_video(url))

    def test_m_youtube_playlist_url(self):
        url = "https://m.youtube.com/playlist?list=PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt"
        self.assertFalse(self.check_is_single_video(url))

if __name__ == "__main__":
    unittest.main()
