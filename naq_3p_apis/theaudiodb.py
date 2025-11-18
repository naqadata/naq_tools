from dataclasses import dataclass
from enum import Enum
from typing import Generator

from naq_3p_apis.api import Api
from naq_3p_apis.exceptions import ArtistNotFound, TrackNotFound
from naq_utils.logging import logger
from naq_utils.caching import RequestCache
from naq_utils.settings import JsonFile

THEAUDIODB_URL = "https://theaudiodb.p.rapidapi.com/"


class AliasCategory(Enum):
    Artist = "artist"
    SongTitle = "song_title"


class ManualInfo:
    _artist_cache = RequestCache("manual-info-artist-cache")
    _track_cache = RequestCache("manual-info-track-cache")

    @classmethod
    def cached_artist_info(cls, artist_name: str) -> dict | None:
        return cls._artist_cache.get(artist_name)

    @classmethod
    def cached_track_info(cls, artist_name: str, song_title: str) -> dict | None:
        return cls._track_cache.get([artist_name, song_title])

    @classmethod
    def artist_info(cls, artist_name: str) -> dict | None:
        manual_info = cls.cached_artist_info(artist_name)
        if manual_info:
            return manual_info

        logger.warning("Entering artist details manually. Ctrl-C to skip altogether.")

        try:
            artist_name = input(f"Enter artist name manually (or Enter to accept '{artist_name}'): ") or artist_name
            description = input(f"Enter artist description manually (or Enter to leave blank): ") or ""
            art_url = input("Enter URL to artist thumbnail artwork (or Enter to leave blank): ") or ""
        except KeyboardInterrupt:
            return None

        manual_info = {
            "strArtist": artist_name,
            "strBiographyEN": description,
            "strArtistThumb": art_url
        }

        cls._artist_cache.cache(artist_name, manual_info)
        return manual_info

    @classmethod
    def track_info(cls, artist_name: str, song_title: str) -> dict | None:
        manual_info = cls.cached_track_info(artist_name, song_title)
        if manual_info:
            return manual_info

        logger.warning("Entering track details manually. Ctrl-C to skip altogether.")

        try:
            artist_name = input(f"Enter manual artist (or enter to accept '{artist_name}'): ") or artist_name
            song_title = input(f"Enter manual title (or enter to accept '{song_title}'): ") or song_title
            description = input(f"Enter manual description (or enter to leave blank): ") or ""
            genre = input(f"Enter manual genre (or enter to leave blank): ") or ""
            yt_link = input(f"Enter YouTube link (or enter to leave blank): ") or ""
        except KeyboardInterrupt:
            return None

        manual_info = {
            "strTrack": song_title,
            "strArtist": artist_name,
            "strDescriptionEN": description,
            "strGenre": genre,
            "strMusicVid": yt_link,
            "intScore": "0.0"
        }

        cls._track_cache.cache([artist_name, song_title], manual_info)
        return manual_info


# noinspection DuplicatedCode
class TheAudioDb(Api):
    _manual_track_infos = {}
    _http_pool = None

    def __init__(self, api_key: str, interactive: bool = False):
        super().__init__("theaudiodb", api_key, THEAUDIODB_URL)        
        self._alias_file = JsonFile("audiodb_aliases")
        self.interactive = interactive

    def save_alias(self, category: AliasCategory, original: str, alias: str):
        alias_set_list: list[list[str]] = self._alias_file.setdefault(category.value, [])

        for alias_set in alias_set_list:
            if original in alias_set:
                alias_set.append(alias)
        else:
            new_set_list = [original, alias]
            alias_set_list.append(new_set_list)

        self._alias_file[category.value] = alias_set_list
        self._alias_file.save()

    def get_aliases(self, category: AliasCategory, original: str) -> list[str]:
        alias_set_list: list[list[str]] = self._alias_file.setdefault(category.value, [])
        found_alias_set = None

        for alias_set in alias_set_list:
            if original in alias_set:
                found_alias_set = alias_set.copy()

        if found_alias_set:
            found_alias_set.remove(original)
            return found_alias_set

        return []

    def get_artist_info(self, artist_id: str, update_cache: bool = False) -> dict | None:
        response = self._request("artist.php", {"i": artist_id}, update_cache=update_cache)
        if response and response["artists"]:
            return response["artists"][0]

    def get_album_info(self, album_id: str, update_cache: bool = False) -> dict | None:
        response = self._request("album.php", {"m": album_id}, update_cache=update_cache)
        if response and response["album"]:
            return response["album"][0]

    def get_track_info(self, artist_name: str, song_title: str, update_cache: bool = False) -> dict | None:
        # apply previously entered corrections
        artist_alises = self.get_aliases(AliasCategory.Artist, artist_name)
        song_aliases = self.get_aliases(AliasCategory.SongTitle, song_title)

        logger.info(f"Searching TheAudioDB for '{song_title}' by '{artist_name}'")

        for cur_artist_name in [artist_name] + artist_alises:
            for cur_song_title in [song_title] + song_aliases:
                response = self._request("searchtrack.php", {"s": cur_artist_name, "t": cur_song_title}, update_cache=update_cache)

                if response and response['track']:
                    return response['track'][0]

                cached_manual_info = ManualInfo.cached_track_info(cur_artist_name, cur_song_title)
                if cached_manual_info:
                    return cached_manual_info

        if not self.interactive:
            return None

        logger.warning(f"Track not found for '{song_title}' by '{artist_name}'. Provide alternates or Ctrl-C to enter info manually.")

        while True:
            try:
                new_artist_name = input(f"Enter alternate artist (Enter to accept '{artist_name}'): ") or artist_name
                new_song_title = input(f"Enter corrected title (Enter to accept '{song_title}'): ") or song_title
            except KeyboardInterrupt:
                print("")
                return ManualInfo.track_info(artist_name, song_title)

            response = self._request("searchtrack.php", {"s": new_artist_name, "t": new_song_title})
            if response and response['track']:
                if new_artist_name != artist_name:
                    self.save_alias(AliasCategory.Artist, artist_name, new_artist_name)
                if new_song_title != song_title:
                    self.save_alias(AliasCategory.SongTitle, song_title, new_song_title)

                return response["track"][0]
            
    @dataclass
    class _MusicVideo:
        url: str
        song_title: str

    def music_videos_for_artist(self, artist_id: str) -> Generator[_MusicVideo, None, None]:
        artist_info = self.get_artist_info(artist_id)
        assert artist_info, f"No artist returned for ID: {artist_id}"

        response = self._request("mvid.php", {"i": artist_info["idArtist"]})
        if not response or not response["mvids"]:
            logger.warning("No videos found for ID", value=artist_id)
            return

        # pre-sort the json entries
        for mvid in sorted(response["mvids"], key=lambda x: x["idTrack"]):
            youtube_url = mvid.get("strMusicVid")
            song_title = mvid.get("strTrack")
            if youtube_url and song_title:
                yield self._MusicVideo(youtube_url, song_title) 
