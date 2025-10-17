class TheAudioDBException(Exception):
    ...


class ArtistNotFound(TheAudioDBException):
    def __init__(self, artist_name: str):
        super().__init__(f"No artist info found in TheAudioDB for '{artist_name}'")


class TrackNotFound(TheAudioDBException):
    def __init__(self, artist_name: str, song_name: str):
        super().__init__(f"No track info found in TheAudioDB for song '{song_name}' by '{artist_name}'")


class PlexException(Exception):
    ...


class ArtistNotFoundInPlex(PlexException):
    def __init__(self, artist_name: str):
        super().__init__(f"Could not locate artist '{artist_name}' in Plex")


class VideoNotFoundInPlex(PlexException):
    def __init__(self, artist_name: str, episode_num: int):
        super().__init__(f"Could not locate episode {episode_num} of '{artist_name}' in Plex")


class SkipVideo(Exception):
    def __init__(self):
        super().__init__("Skipping video")
