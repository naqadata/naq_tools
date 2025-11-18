from naq_video_downloader.youtube_music_video import MusicVideo
from naq_video_downloader.settings import GlobalSettings
from naq_utils.extensions import Path
from datetime import date
import pytest
import tempfile
import os
import urllib.parse


PLAYLIST_ID = "PLmyAPRLQRJ6lMbAdXYGuyZ627Y9RoX25i"
LIVE_VIDEO_ID = "Fpn1imb9qZg"  # https://www.youtube.com/watch?v=Fpn1imb9qZg - Coldplay - A Sky Full Of Stars (Live at River Plate)
OFFICIAL_VIDEO_ID = "VPRjCeoBqrI"  # https://www.youtube.com/watch?v=VPRjCeoBqrI - Coldplay - A Sky Full Of Stars (Official Video)


@pytest.fixture(autouse=True)
def test_setup():
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    assert google_api_key, "Must set GOOGLE_API_KEY env var before running tests"

    imvdb_api_key = os.environ.get("IMVDB_API_KEY")
    assert imvdb_api_key, "Must set IMVDB_API_KEY env var before running tests"

    audiodb_api_key = os.environ.get("AUDIODB_API_KEY")
    assert audiodb_api_key, "Must set AUDIODB_API_KEY env var before running tests"

    GlobalSettings().google_api_key.value = google_api_key
    GlobalSettings().imvdb_api_key.value = imvdb_api_key
    GlobalSettings().audiodb_api_key.value = audiodb_api_key

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        GlobalSettings().download_dir.value = tmp_dir
        yield


@pytest.fixture
def live_music_video():
    yield MusicVideo.from_youtube_id(LIVE_VIDEO_ID)

@pytest.fixture
def official_music_video():
    yield MusicVideo.from_youtube_id(OFFICIAL_VIDEO_ID)


class TestMusicVideo:
    def test_from_youtube_id(self, live_music_video: MusicVideo):
        assert live_music_video
        assert live_music_video.artist_name == "Coldplay"
        assert live_music_video.song_title == "A Sky Full Of Stars"
        assert live_music_video.title == "A Sky Full Of Stars (Live at River Plate)"
    
    def test_video_count(self, live_music_video: MusicVideo):
        assert live_music_video.view_count > 100000000

    def test_download(self, live_music_video: MusicVideo):
        live_music_video.download()
        assert live_music_video.downloaded
        assert live_music_video.artist_download_path.existsi()
        assert live_music_video.artist_thumbnail_path.existsi()
        assert live_music_video.download_path.existsi()
        assert live_music_video.download_path.is_relative_to(live_music_video.artist_download_path)

    def test_imvdb_info(self, official_music_video: MusicVideo):
        assert official_music_video._imvdb_info
    
    def test_audiodb_info(self, official_music_video: MusicVideo):
        assert official_music_video._audiodb_info

    def test_info_values(self, official_music_video: MusicVideo):
        assert official_music_video.artist_audiodb_id == "111239" # Coldplay
        assert official_music_video.artist_name == "Coldplay"
        assert official_music_video.artist_name in str(official_music_video.artist_download_path)
        assert official_music_video.album_audiodb_id == "2205903" # Ghost Stories
        assert official_music_video.album_name == "Ghost Stories"
        assert official_music_video.audiodb_id == "33899812"
        assert official_music_video.year == 2014
        assert official_music_video.release_date == date(2014, 6, 19)
        assert official_music_video.description and "is a song recorded by British alternative rock band Coldplay" in official_music_video.description
        assert official_music_video.album_name == "Ghost Stories"
        assert official_music_video.thumbnail_url and urllib.parse.urlparse(official_music_video.thumbnail_url)
        assert official_music_video.album_thumbnail_url and urllib.parse.urlparse(official_music_video.album_thumbnail_url)
        assert official_music_video.artist_thumbnail_url and urllib.parse.urlparse(official_music_video.artist_thumbnail_url)

