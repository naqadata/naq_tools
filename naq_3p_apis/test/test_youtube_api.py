import pytest
import os

import pyyoutube

from naq_3p_apis.youtube_api import YouTubeAPI


pytestmark = pytest.mark.integration


@pytest.fixture()
def api():
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    assert google_api_key, "Must set GOOGLE_API_KEY env var before running tests"

    return YouTubeAPI(google_api_key)


class TestYoutubeApi:
    PLAYLIST_ID = "PLmyAPRLQRJ6lMbAdXYGuyZ627Y9RoX25i"
    VIDEO_ID = "TIy3n2b7V9k"

    def test_get_playlist(self, api: YouTubeAPI):
        playlist = api.get_playlist(self.PLAYLIST_ID)
        assert playlist
        assert playlist.id == self.PLAYLIST_ID

    def test_get_video(self, api: YouTubeAPI):
        video = api.get_video(self.VIDEO_ID)
        assert video
        assert video.id == self.VIDEO_ID

    def test_iter_playlist_items(self, api: YouTubeAPI):
        videos = list(api.iter_playlist_videos(self.PLAYLIST_ID))
        assert videos
        assert len(videos) > 100
        for video in videos:
            assert isinstance(video, pyyoutube.Video)
