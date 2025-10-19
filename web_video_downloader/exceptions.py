class TheAudioDBException(Exception):
    ...


class ArtistNotFound(TheAudioDBException):
    def __init__(self, artist_name: str):
        super().__init__(f"No artist info found in TheAudioDB for '{artist_name}'")


class TrackNotFound(TheAudioDBException):
    def __init__(self, artist_name: str, song_name: str):
        super().__init__(f"No track info found in TheAudioDB for song '{song_name}' by '{artist_name}'")


class SkipVideo(Exception):
    def __init__(self):
        super().__init__("Skipping video")
