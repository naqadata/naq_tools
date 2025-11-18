import json
import pickle
import shutil
import tempfile
from hashlib import md5
from threading import Lock
from typing import Any, Generator, Hashable, TypeAlias

from naq_utils.constants import  HOME_SAVE_DIR
from naq_utils.extensions import Path


class RequestCache:
    CACHE_DIR = Path.home() / ".cache" / "naq_tools"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    Key: TypeAlias = str | list | dict

    def __init__(self, cache_name: str):
        self.path = self.CACHE_DIR / cache_name
        self._lock = Lock()
        self._cache: dict[str, Any] = {}

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
    def _get_key_hash(cls, key: Key, gen = None) -> str:
        md5_gen = gen or md5()

        if isinstance(key, str):
            md5_gen.update(key.encode("utf-8"))
        elif isinstance(key, list):
            for item in key:
                md5_gen.update(cls._get_key_hash(item, md5_gen).encode())
        elif isinstance(key, dict):
            md5_gen.update(json.dumps(key).encode())

        return md5_gen.hexdigest()

    def get(self, key: Key) -> Any | None:
        return self._cache.get(self._get_key_hash(key), None)

    def cache(self, key: Key, response: Any):
        self._cache[self._get_key_hash(key)] = response
        self._save()

    def delete(self, key: Key) -> bool:
        """Delete the key from the cache, if found. Return if something was deleted or not."""
        hash = self._get_key_hash(key)
        if hash in self._cache:
            del self._cache[hash]
            return True
        return False