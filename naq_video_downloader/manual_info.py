from typing import Dict, Optional
from naq_utils import custom_logging as logging
from naq_video_downloader.utils import RequestCache
from naq_video_downloader.exceptions import SkipVideo


class ManualInfo:
    _artist_cache = RequestCache("manual-info-artist-cache")
    _track_cache = RequestCache("manual-info-track-cache")

    @classmethod
    def cached_artist_info(cls, artist_name: str) -> Optional[Dict]:
        return cls._artist_cache.get_response(artist_name)

    @classmethod
    def cached_track_info(cls, artist_name: str, song_title: str) -> Optional[Dict]:
        return cls._track_cache.get_response([artist_name, song_title])

    @classmethod
    def artist_info(cls, artist_name: str) -> Dict:
        manual_info = cls.cached_artist_info(artist_name)
        if manual_info:
            return manual_info

        logging.warning("Entering artist details manually. Ctrl-C to skip altogether.")

        try:
            artist_name = input(f"Enter artist name manually (or Enter to accept '{artist_name}'): ") or artist_name
            description = input(f"Enter artist description manually (or Enter to leave blank): ") or ""
            art_url = input("Enter URL to artist thumbnail artwork (or Enter to leave blank): ") or ""
        except KeyboardInterrupt:
            raise SkipVideo()

        manual_info = {
            "strArtist": artist_name,
            "strBiographyEN": description,
            "strArtistThumb": art_url
        }

        cls._artist_cache.cache_response(artist_name, manual_info)
        return manual_info

    @classmethod
    def track_info(cls, artist_name: str, song_title: str) -> Dict:
        manual_info = cls.cached_track_info(artist_name, song_title)
        if manual_info:
            return manual_info

        logging.warning("Entering track details manually. Ctrl-C to skip altogether.")

        try:
            artist_name = input(f"Enter manual artist (or enter to accept '{artist_name}'): ") or artist_name
            song_title = input(f"Enter manual title (or enter to accept '{song_title}'): ") or song_title
            description = input(f"Enter manual description (or enter to leave blank): ") or ""
            genre = input(f"Enter manual genre (or enter to leave blank): ") or ""
            yt_link = input(f"Enter YouTube link (or enter to leave blank): ") or ""
        except KeyboardInterrupt:
            raise SkipVideo

        manual_info = {
            "strTrack": song_title,
            "strArtist": artist_name,
            "strDescriptionEN": description,
            "strGenre": genre,
            "strMusicVid": yt_link,
            "intScore": "0.0"
        }

        cls._track_cache.cache_response([artist_name, song_title], manual_info)
        return manual_info
