from typing import Dict, Generator
from naq_utils.custom_logging import logger
from naq_video_downloader.theaudiodb import TheAudioDBAPI
from naq_video_downloader.utils import GlobalSettings
from naq_video_downloader.library_item import LibraryItem
from pathlib import Path
import re


class Artist(LibraryItem):
    def __init__(self, name: str):
        audiodb_info = TheAudioDBAPI.artist_info(name) or {}
        super().__init__(audiodb_info)

    def __repr__(self) -> str:
        return f"<Artist {self.name}>"

    @property
    def name(self) -> str:
        return re.sub(r"[/]", " ", self._audiodb_info["strArtist"]).strip()

    @classmethod
    def from_found_obj_files(cls, *args, **kwargs) -> Generator["Artist", None, None]:
        for library_item in super().from_found_obj_files("Artist"):
            assert isinstance(library_item, Artist)
            yield library_item

    @property
    def download_path(self) -> Path:
        path = GlobalSettings().download_dir / re.sub(r"/", " ", self.name)
        path.mkdir(exist_ok=True, parents=True)
        return path

    def save_nfo_file(self):
        from xml.etree import ElementTree as ET

        nfo_path = self.download_path / f"artist.nfo"

        if not nfo_path.exists():
            logger.info(f"Writing NFO for", value=self)

            root = ET.Element("artist")

            if self._audiodb_info:
                name_elem = ET.SubElement(root, "name")
                name_elem.text = self._audiodb_info["strArtist"]

                biography_elem = ET.SubElement(root, "biography")
                biography_elem.text = self._audiodb_info["strBiographyEN"]

                audiodb_artist_id = ET.SubElement(root, "audiodbartistid")
                audiodb_artist_id.text = self._audiodb_info["idArtist"]

            tree = ET.ElementTree(root)
            ET.indent(tree)
            tree.write(nfo_path, encoding="utf-8", xml_declaration=True)

    @property
    def art_url(self) -> str:
        return self._audiodb_info["strArtistThumb"]

    @property
    def metadata(self) -> Dict:
        return {
            'title.value': self.name,
            'summary.value': self._audiodb_info.get("strBiographyEN") or self._audiodb_info.get("strBiography") or "",
        }
