import shutil

import os
import re
from pathlib import Path
import pickle
from typing import List, Optional, Dict, Union, Generator
from hashlib import md5
import json
import tempfile
from collections import namedtuple
from shared_memory_dict import SharedMemoryDict
from multiprocessing import resource_tracker
from threading import Lock
import urllib3


HOME_SAVE_DIR = Path.home() / ".naq_video_downloader"
HOME_SAVE_DIR.mkdir(exist_ok=True)


MatchedTitle = namedtuple("MatchedTitle", ["artist_name", "song_title", "full_song_title"])


def match_title(title: str) -> Optional[MatchedTitle]:
    if " - " not in title:
        return None

    artist_name, full_song_title = title.split(" - ", maxsplit=1)

    match_regexes = [
        r"((.+))\s+\(.*official.+(?:video|version|visualiser)\)",
    ]

    if GlobalSettings().permissive:
        match_regexes.extend([
            r"((.+)\s+\(\w+\s+\d\d\d\d\))",
            r"((.+)\s+\(live\s(?:in|at|from).+\))",
            r"((.+))",
        ])

    ignore_regexes = [
        r".+behind\sthe\sscenes",
        r"((.+)\s+\(official.+lyric.+(?:video|version|visualiser)\))",
        r".+reacts\sto.+"
    ]

    for regex in ignore_regexes:
        if re.match(regex, full_song_title, flags=re.IGNORECASE) is not None:
            return None

    for match_regex in match_regexes:
        match = re.match(match_regex, full_song_title, flags=re.IGNORECASE)
        if match is not None:
            full_title, song_title = match.groups()
            song_title = song_title.replace("/", "-")
            return MatchedTitle(artist_name, song_title, full_title)

    if GlobalSettings().interactive:
        print(f"No match found for '{title}'")
        artist_name = input("Enter Artist Name: ")
        song_title = input("Enter Song Title: ")
        return MatchedTitle(artist_name, song_title, song_title)


class SettingsFile:
    def __init__(self, filename: str):
        self._path = HOME_SAVE_DIR / filename
        self.settings: Dict = {}

        if self._path.exists():
            with self._path.open("r") as f:
                self.settings: Dict = json.load(f)

    def save(self) -> None:
        with self._path.open("w") as f:
            json.dump(self.settings, f, indent=2)


class GlobalSettings:
    def __init__(self):
        self._smd = SharedMemoryDict(name=f"{os.getpid()}-global-settings", size=8192)
        resource_tracker.unregister(f"/{self._smd.shm.name}", "shared_memory")

    @property
    def download_dir(self) -> Path:
        path_str = self._smd.get("download_dir")
        return Path(path_str)

    @download_dir.setter
    def download_dir(self, value: Path):
        self._smd["download_dir"] = str(value)

    @property
    def interactive(self) -> bool:
        return self._smd.get("interactive", False)

    @interactive.setter
    def interactive(self, value: bool):
        self._smd["interactive"] = value

    @property
    def permissive(self) -> bool:
        return self._smd.get("permissive", False)

    @permissive.setter
    def permissive(self, value: bool):
        self._smd["permissive"] = value

    @property
    def print_index(self) -> Optional[int]:
        return self._smd.get("print_index", None)

    @print_index.setter
    def print_index(self, value: Optional[int]):
        self._smd["print_index"] = value

    @property
    def min_view_count(self) -> int:
        return self._smd.get("min_view_count", 0)

    @min_view_count.setter
    def min_view_count(self, value: Optional[int]):
        self._smd["min_view_count"] = value


class RequestCache:
    CACHE_DIR = HOME_SAVE_DIR / ".request_cache"
    CACHE_DIR.mkdir(exist_ok=True)

    Key = Union[str, List, Dict]

    def __init__(self, cache_name: str):
        self.path = self.CACHE_DIR / cache_name
        self._lock = Lock()
        self._cache = {}

        self._load()

    def _load(self):
        if self.path.exists():
            with self.path.open("rb") as f:
                self._cache = pickle.load(f)
        else:
            self._cache = {}

    def _save(self):
        with self._lock:
            # write the cache to a temp file, in case we are interrupted in the process of saving
            # then, we will move the temp file in place of the cache file, narrowing or closing the window of potential corruption
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_file = Path(tmp_dir) / self.path.name
                with tmp_file.open("wb") as f:
                    pickle.dump(self._cache, f)
                shutil.move(tmp_file, self.path)

    @classmethod
    def _hash_key(cls, key: Key, gen: md5 = None) -> str:
        md5_gen = gen or md5()

        if isinstance(key, str):
            md5_gen.update(key.encode("utf-8"))
        elif isinstance(key, List):
            for item in key:
                md5_gen.update(cls._hash_key(item, md5_gen).encode())
        elif isinstance(key, Dict):
            md5_gen.update(json.dumps(key).encode())

        return md5_gen.hexdigest()

    def get_responses(self, key: Key) -> List[Dict]:
        return self._cache.get(self._hash_key(key), [])

    def get_response(self, key: Key) -> Optional[Dict]:
        responses = self.get_responses(key)
        return responses[0] if responses else None

    def cache_responses(self, key: Key, responses: List[Dict]):
        self._cache[self._hash_key(key)] = responses
        self._save()

    def cache_response(self, key: Key, response: Dict):
        self.cache_responses(key, [response])

    def delete_response(self, key: Key):
        self._cache.pop(self._hash_key(key), False)

    def iter_responses(self) -> Generator[Dict, None, None]:
        for response in self._cache.values():
            yield response


def fetch_art(url: str, save_dir: Path, filename: str = "poster"):
    http = urllib3.PoolManager()
    req = http.request("GET", url, preload_content=False)

    art_path = save_dir / f"{filename}.jpg"

    save_dir.mkdir(exist_ok=True, parents=True)

    if art_path.exists():
        return

    with art_path.open("wb") as f:
        while True:
            data = req.read(1024)
            if not data:
                break
            f.write(data)
    req.release_conn()
