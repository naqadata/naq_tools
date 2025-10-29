from naq_video_downloader.__main__ import TheAudioDBAPI


def test_artist_info():
    api = TheAudioDBAPI("Coldplay")
    assert api is not None
    assert api.artist_info is not None
    assert api.artist_info is not None
    assert api.artist_info["artists"][0]["strArtist"] == "Coldplay"
    assert api._artist_id is not None and api._artist_id == api.artist_info["idArtist"]


def test_artist_videos():
    api = TheAudioDBAPI("Coldplay")
    assert api.videos is not None
    assert len(api.videos) > 1

    found = False
    for video in api.videos:
        if video.title == "Biutyful":
            found = True
    assert found
