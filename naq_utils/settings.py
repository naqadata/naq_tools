import os
import json
from multiprocessing import resource_tracker
from typing import TypeAlias

from shared_memory_dict import SharedMemoryDict

from naq_utils.extensions import Path
from naq_utils.constants import HOME_SAVE_DIR


class JsonFile(dict):
    _decoder_class: type[json.JSONDecoder] | None = None
    _encoder_class: type[json.JSONEncoder] | None = None

    def __init__(self, name: str):
        super().__init__()
        self._path = HOME_SAVE_DIR / f"{name}.json"
        
        if self._path.exists():
            with self._path.open("r") as f:
                self.update(json.load(f, cls=self._decoder_class))

    def save(self) -> None:
        with self._path.open("w") as f:
            json.dump(self, f, indent=2, cls=self._encoder_class)


class GlobalSetting[T]:
    def __init__(self, name: str, default: T):
        self.name = name
        self.default = default

        self._smd = SharedMemoryDict(name=f"{os.getpid()}-global-settings", size=65535)
        resource_tracker.unregister(f"/{self._smd.shm.name}", "shared_memory")

    @property
    def value(self) -> T:
        return self._smd.get(self.name, self.default)
    
    @value.setter
    def value(self, v: T):
        self._smd[self.name] = v


GSStr: TypeAlias = GlobalSetting[str]
GSStrOrNone: TypeAlias = GlobalSetting[str | None]
GSInt: TypeAlias = GlobalSetting[int]
GSIntOrNone: TypeAlias = GlobalSetting[int | None]
GSBool: TypeAlias = GlobalSetting[bool]
GSBoolOrNone: TypeAlias = GlobalSetting[bool | None]
GSPath: TypeAlias = GlobalSetting[Path]
GSPathOrNone: TypeAlias = GlobalSetting[Path | None]
