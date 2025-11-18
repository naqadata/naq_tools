from naq_video_downloader.youtube_video import YouTubeVideo
from naq_video_downloader.settings import GlobalSettings
from naq_utils.extensions import Path
from datetime import date
import pytest
import tempfile
import os
import urllib.parse


PLAYLIST_ID = "PLYbocufkwRFA1cz_N8epnI10--gPwzzKu"  # Pop-up Videos
VIDEO_ID = "L8C_JvJfxfU"  # https://www.youtube.com/watch?v=L8C_JvJfxfU - Steve Jobs Memorial Concert with Coldplay


@pytest.fixture(autouse=True)
def test_setup():
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    assert google_api_key, "Must set GOOGLE_API_KEY env var before running tests"

    GlobalSettings().google_api_key.value = google_api_key

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        GlobalSettings().download_dir.value = tmp_dir
        yield


@pytest.fixture
def video():
    yield YouTubeVideo.from_youtube_id(VIDEO_ID)


class TestMusicVideo:
    def test_from_youtube_id(self, video: YouTubeVideo):
        assert video
        assert video.name == "Coldplay live A celebration of Steve jobs memorial 2011 HD"
        assert video.title == "Coldplay live A celebration of Steve jobs memorial 2011 HD"
        assert video.youtube_url == f"https://www.youtube.com/watch?v={VIDEO_ID}"
    
    def test_video_count(self, video: YouTubeVideo):
        assert video.view_count > 100000

    def test_download(self, video: YouTubeVideo):
        assert not video.downloaded
        file_paths = video.download()
        assert video.downloaded

        for path in file_paths:
            if path.suffix == ".nfo":
                break
        else:
            assert False, "Failed to find NFO file when downloading video"


