from typing import Optional, Dict, Tuple, Union, List
import urllib3
import urllib.parse
import json
from enum import Enum
import os

from naq_utils.custom_logging import logger
from naq_video_downloader.utils import RequestCache, SettingsFile, GlobalSettings
from naq_video_downloader.manual_info import ManualInfo
from naq_video_downloader.exceptions import ArtistNotFound, TrackNotFound

THEAUDIODB_URL = "https://theaudiodb.p.rapidapi.com/"


class AliasCategory(Enum):
    Artist = "artist"
    SongTitle = "song_title"

# noinspection DuplicatedCode
class TheAudioDBAPI:
    _cache = RequestCache("theaudiodb-api")
    _alias_file = SettingsFile(".aliases")
    _manual_track_infos = {}
    _http_pool = None

    @classmethod
    def save_alias(cls, category: AliasCategory, original: str, alias: str):
        alias_set_list: List[List[str]] = cls._alias_file.settings.setdefault(category.value, [])

        for alias_set in alias_set_list:
            if original in alias_set:
                alias_set.append(alias)
        else:
            new_set_list = [original, alias]
            alias_set_list.append(new_set_list)

        cls._alias_file.settings[category.value] = alias_set_list
        cls._alias_file.save()

    @classmethod
    def get_aliases(cls, category: AliasCategory, original: str) -> List[str]:
        alias_set_list: List[List[str]] = cls._alias_file.settings.setdefault(category.value, [])
        found_alias_set = None

        for alias_set in alias_set_list:
            if original in alias_set:
                found_alias_set = alias_set.copy()

        if found_alias_set:
            found_alias_set.remove(original)
            return found_alias_set

        return []

    @classmethod
    def _request(cls, path: str, params: Dict[str, str], update_cache: bool = False):
        headers = {
            "x-rapidapi-host": "theaudiodb.p.rapidapi.com",
            "x-rapidapi-key": GlobalSettings().audiodb_api_key
        }

        if update_cache:
            cls._cache.delete_response([path, params])

        cached_response = cls._cache.get_response([path, params])
        if cached_response:
            return cached_response

        arg_string = urllib.parse.urlencode(params) if params else ""
        url = urllib.parse.urljoin(THEAUDIODB_URL, path) + f"?{arg_string}"

        logger.debug(f"Requesting '{url}'")

        if cls._http_pool is None:
            cls._http_pool = urllib3.PoolManager()
        response = cls._http_pool.request("GET", url, headers=headers)
        assert response.status == 200, f"Bad response ({response.status}): {response.data}"
        response_json = json.loads(response.data)

        cls._cache.cache_response([path, params], response_json)

        return response_json

    @classmethod
    def artist_info(cls, artist_name: str) -> Optional[Dict]:
        # apply previously entered corrections
        aliases = cls.get_aliases(AliasCategory.Artist, artist_name)

        for artist_name in [artist_name] + aliases:
            response = cls._request("search.php", {"s": artist_name})
            if response["artists"]:
                return response["artists"][0]

            cached_manual_info = ManualInfo.cached_artist_info(artist_name)
            if cached_manual_info:
                return cached_manual_info

        if not GlobalSettings().interactive:
            raise ArtistNotFound(artist_name)

        # ask user for a correction
        logger.warning(f"Artist not found for '{artist_name}'. Provide alternate name or Ctrl-C to enter info manually.")
        while True:
            try:
                new_artist_name = input("Enter alternate artist name: ")
            except KeyboardInterrupt:
                print("")
                return ManualInfo.artist_info(artist_name)

            response = cls._request("search.php", {"s": new_artist_name})
            if response["artists"]:
                cls.save_alias(AliasCategory.Artist, artist_name, new_artist_name)
                return response["artists"][0]

    @classmethod
    def album_info(cls, album_id: str, update_cache: bool = False) -> Optional[Dict]:
        response = cls._request("album.php", {"m": album_id}, update_cache=update_cache)
        if response["album"]:
            return response["album"][0]

    @classmethod
    def track_info(cls, artist_name: str, song_title: str, update_cache: bool = False) -> Optional[Dict]:
        # apply previously entered corrections
        artist_alises = cls.get_aliases(AliasCategory.Artist, artist_name)
        song_aliases = cls.get_aliases(AliasCategory.SongTitle, song_title)

        for cur_artist_name in [artist_name] + artist_alises:
            for cur_song_title in [song_title] + song_aliases:
                response = cls._request("searchtrack.php", {"s": cur_artist_name, "t": cur_song_title}, update_cache=update_cache)

                if response['track']:
                    return response['track'][0]

                cached_manual_info = ManualInfo.cached_track_info(cur_artist_name, cur_song_title)
                if cached_manual_info:
                    return cached_manual_info

        if not GlobalSettings().interactive:
            raise TrackNotFound(artist_name, song_title)

        logger.warning(f"Track not found for '{song_title}' by '{artist_name}'. Provide alternates or Ctrl-C to enter info manually.")

        while True:
            try:
                new_artist_name = input(f"Enter alternate artist (Enter to accept '{artist_name}'): ") or artist_name
                new_song_title = input(f"Enter corrected title (Enter to accept '{song_title}'): ") or song_title
            except KeyboardInterrupt:
                print("")
                return ManualInfo.track_info(artist_name, song_title)

            response = cls._request("searchtrack.php", {"s": new_artist_name, "t": new_song_title})
            if response['track']:
                if new_artist_name != artist_name:
                    cls.save_alias(AliasCategory.Artist, artist_name, new_artist_name)
                if new_song_title != song_title:
                    cls.save_alias(AliasCategory.SongTitle, song_title, new_song_title)

                return response["track"][0]

    @classmethod
    def mvids(cls, artist_name: str):
        artist_info = cls.artist_info(artist_name)

        response = cls._request("mvid.php", {"i": artist_info["idArtist"]})
        if not response["mvids"]:
            logger.warning("No videos found for", value=artist_name)
            return

        # pre-sort the json entries
        for mvid in sorted(response["mvids"], key=lambda x: x["idTrack"]):
            yield mvid


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["analyze"])
    args = parser.parse_args()

    album_ids = set()

    have_amzon_id = 0

    if args.command == "analyze":
        try:
            for response in TheAudioDBAPI._cache.iter_responses():
                if "album" in response[0]:
                    try:
                        amazon_id = response[0]["album"][0]["strAmazonID"]
                    except:
                        continue
                    if amazon_id:
                        have_amzon_id += 1
        except KeyboardInterrupt:
            pass

        print(have_amzon_id)

        # for fmt, count in release_format_counts.most_common():
        #     pct = (float(count) / float(num_albums)) * 100.0
        #     print(f"{count:4}  [{pct:3.1f}%]: {fmt}")


if __name__ == "__main__":
    main()
