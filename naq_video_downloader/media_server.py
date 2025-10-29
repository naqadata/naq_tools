class MediaServer:
    def __init__(self, library_name: str):
        self.library_name = library_name

    def update_library(self, update_cache_for_artist: str = None):
        raise NotImplementedError()
