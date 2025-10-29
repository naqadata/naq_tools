from typing import Generator
from pathlib import Path
from naq_video_downloader.utils import HOME_SAVE_DIR
import pickle


class LibraryItem:
    class ObjectFile:
        OBJ_FILE_DIR = HOME_SAVE_DIR / ".object-files"

        def __init__(self, path: Path = None, category: str = None, name: str = None):
            assert path or (category and name), f"Must pass either path, or category & name"

            if path:
                self.path = path
            else:
                category_path = self.OBJ_FILE_DIR / category
                category_path.mkdir(exist_ok=True, parents=True)
                self.path = category_path / f"{name}.obj"

        @classmethod
        def search(cls, category: str, pattern: str) -> Generator["LibraryItem", None, None]:
            category_path = cls.OBJ_FILE_DIR / category
            for obj_file in category_path.rglob(pattern):
                with obj_file.open("rb") as f:
                    yield pickle.load(f)

        def read(self) -> "LibraryItem | None":
            if self.path.exists():
                with open(self.path, "rb") as f:
                    return pickle.load(f)
            return None

        def save(self, item: "LibraryItem"):
            with open(self.path, "wb") as f:
                pickle.dump(item, f)

    def __init__(self, audiodb_info: dict):
        self._audiodb_info = audiodb_info

    @classmethod
    def from_found_obj_files(cls, category: str = None) -> Generator["LibraryItem", None, None]:
        path = cls.ObjectFile.OBJ_FILE_DIR / category if category else cls.ObjectFile.OBJ_FILE_DIR

        for entry in path.rglob("*.obj"):
            with entry.open("rb") as f:
                library_item = pickle.load(f)
                assert isinstance(library_item, LibraryItem)
                yield library_item

    @property
    def download_path(self) -> Path:
        raise NotImplementedError()

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def metadata(self) -> dict:
        return {
            'audiodb': self._audiodb_info
        }

    @classmethod
    def from_obj_file(cls, path: Path) -> "LibraryItem | None":
        return cls.ObjectFile(path=path).read()

    def save_obj_file(self):
        self.ObjectFile(category=self.__class__.__name__, name=self.name).save(self)
