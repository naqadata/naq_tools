from dataclasses import dataclass
from typing import Generator
from naq_utils.constants import HOME_SAVE_DIR
from naq_utils.extensions import Path
import pickle


class Serialize:
    @dataclass
    class _ObjectFile:
        path: Path

        @classmethod
        def search(cls, root_dir: Path, pattern: str = "*.obj") -> Generator["Serialize", None, None]:
            for obj_file in root_dir.rglob(pattern):
                with obj_file.open("rb") as f:
                    yield pickle.load(f)

        def read(self) -> "Serialize | None":
            if self.path.exists():
                with open(self.path, "rb") as f:
                    return pickle.load(f)
            return None

        def save(self, item: "Serialize"):
            with open(self.path, "wb") as f:
                pickle.dump(item, f)

    @classmethod
    def from_found_obj_files(cls, root_dir: Path) -> Generator["Serialize", None, None]:
        yield from cls._ObjectFile.search(root_dir=root_dir)

    @classmethod
    def from_obj_file(cls, path: Path) -> "Serialize | None":
        return cls._ObjectFile(path=path).read()

    def save_obj_file(self, path: Path):
        Serialize._ObjectFile(path=path).save(self)

    @property
    def name(self) -> str:
        raise NotImplementedError()
