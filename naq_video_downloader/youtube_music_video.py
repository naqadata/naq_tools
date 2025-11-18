from dataclasses import dataclass
from datetime import date
from typing import Generator
import re
from xml.etree import ElementTree as ET

from naq_3p_apis.http import download_file
from naq_3p_apis.imvdb import IMVDB
from naq_3p_apis.theaudiodb import TheAudioDb
from naq_utils.extensions import Path
from naq_utils.logging import logger
from naq_video_downloader.settings import GlobalSettings
from naq_video_downloader.youtube_video import YouTubeVideo


class MusicVideo(YouTubeVideo):
    def __init__(self, youtube_target: str, artist_name: str, song_title: str, full_title: str | None = None):
        full_title = full_title or song_title
        
        super().__init__(youtube_target, full_title)
        
        self.title = full_title
        self.song_title = song_title
        self.artist_name = artist_name

        self.year_released: int = 0  # use default value of 0 for sorting purposes

        imvdb_api_key = GlobalSettings().imvdb_api_key.value
        assert imvdb_api_key, "Must provide valid IMVDB API Key via GlobalSettings()"
        imvdb = IMVDB(imvdb_api_key)
        self._imvdb_info = imvdb.for_youtube_id([self.artist_name, self.song_title], self.youtube_id)

        audiodb_api_key = GlobalSettings().audiodb_api_key.value
        assert audiodb_api_key, "Must provide valid TheAudioDB API Key via GlobalSettings()"

        audiodb = TheAudioDb(audiodb_api_key)
        self._audiodb_info = audiodb.get_track_info(self.artist_name, self.song_title)
        self._artist_audiodb_info = audiodb.get_artist_info(self.artist_audiodb_id) if self.artist_audiodb_id else None
        self._album_audiodb_info = audiodb.get_album_info(self.album_audiodb_id) if self.album_audiodb_id else None

    def __repr__(self):
        return f"MusicVideo(Artist='{self.artist_name}' Title='{self.title}')" 
    
    @property
    def artist_download_path(self) -> Path:
        return GlobalSettings().download_dir.value / re.sub(r"/", " ", self.artist_name)
    
    @property
    def artist_thumbnail_path(self) -> Path:
        return self.artist_download_path / "poster.jpg"

    @property
    def download_path(self) -> Path:
        return self.artist_download_path / self.song_title / f"{self.song_title}.mp4"
    
    @property
    def album_name(self) -> str | None:
        return self._audiodb_info.get("strAlbum") if self._audiodb_info else None
    
    @property
    def artist_audiodb_id(self) -> str | None:
        return self._audiodb_info.get("idArtist") if self._audiodb_info else None
    
    @property
    def album_audiodb_id(self) -> str | None:
        return self._audiodb_info.get("idAlbum") if self._audiodb_info else None
    
    @property
    def audiodb_id(self) -> str | None:
        return self._audiodb_info.get("idTrack") if self._audiodb_info else None
    
    @property
    def year(self) -> int | None:
        # TODO: Potentially get year from album in audiodb. would have to fetch album info
        return self._imvdb_info.get("year") if self._imvdb_info else None
    
    @property
    def release_date(self) -> date | None:
        timestamp = self._imvdb_info.get("release_date_stamp") if self._imvdb_info else None
        return date.fromtimestamp(timestamp) if timestamp else None
        
    @property
    def description(self) -> str | None:
        return self._audiodb_info.get("strDescriptionEN") if self._audiodb_info else None
    
    @property
    def thumbnail_url(self) -> str | None:
        return self._audiodb_info.get("strTrackThumb") if self._audiodb_info else self._imvdb_info.get("image", {}).values().pop(0, None) if self._imvdb_info else None
    
    @property
    def album_thumbnail_url(self) -> str | None:
        return self._album_audiodb_info.get("strAlbumThumb") if self._album_audiodb_info else None
    
    @property
    def artist_thumbnail_url(self) -> str | None:
        return self._artist_audiodb_info.get("strArtistThumb") if self._artist_audiodb_info else None
    
    @property
    def artist_description(self) -> str | None:
        return self._artist_audiodb_info.get("strBiographyEN") if self._artist_audiodb_info else None
       
    @dataclass
    class _MatchedTitle:
        artist_name: str
        song_title: str
        full_song_title: str

    @staticmethod
    def match_title(title: str) -> _MatchedTitle | None:
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
                return MusicVideo._MatchedTitle(artist_name, song_title, full_title)

        if GlobalSettings().interactive:
            print(f"No match found for '{title}'")
            artist_name = input("Enter Artist Name: ")
            song_title = input("Enter Song Title: ")
            return MusicVideo._MatchedTitle(artist_name, song_title, song_title)
    
    @classmethod
    def from_youtube_video(cls, video: YouTubeVideo) -> "MusicVideo | None":
        match = cls.match_title(video.title) if video else None
        
        if match:
            return cls(video.youtube_id, match.artist_name, match.song_title, match.full_song_title)
    
    @classmethod
    def from_youtube_id(cls, youtube_id: str) -> "MusicVideo | None":
        video = YouTubeVideo.from_youtube_id(youtube_id)
        if video:
            return cls.from_youtube_video(video)
        
    @classmethod
    def audiodb_search_for_more(cls) -> Generator["MusicVideo", None, None]:
        audiodb = TheAudioDb(GlobalSettings().audiodb_api_key.value)

        for path in GlobalSettings().download_dir.value.rglob("artist.nfo"):
            root = ET.parse(path).getroot()
            artist_name_elem = root.find("name")
            artist_audiodb_id_elem = root.find("audiodbartistid")

            if artist_name_elem is not None and artist_audiodb_id_elem is not None:
                artist_name = artist_name_elem.text
                audiodb_id = artist_audiodb_id_elem.text

                if artist_name and audiodb_id:
                    for music_video in audiodb.music_videos_for_artist(audiodb_id):
                        yield MusicVideo(music_video.url, artist_name, music_video.song_title)

    @classmethod
    def youtube_search(cls, query: str) -> Generator["MusicVideo", None, None]:
        for video in cls.youtube_api().search(query):
            if video and video.id:
                music_video = cls.from_youtube_id(video.id)
                if music_video:
                    yield music_video

    def _get_nfo_xml_root(self, video_file_path: Path, thumbnail_file_path: Path | None = None) -> ET.Element:
        root = super()._get_nfo_xml_root(video_file_path, thumbnail_file_path)

        ET.SubElement(root, "artist").text = self.artist_name
        
        if self.album_name:
            ET.SubElement(root, "album").text = self.album_name
        
        if self.artist_audiodb_id:
            ET.SubElement(root, "audiodbartistid").text = self.artist_audiodb_id

        if self.album_audiodb_id:
            ET.SubElement(root, "audiodbalbumid").text = self.album_audiodb_id

        if self.description:
            ET.SubElement(root, "plot").text = self.description

        if self.year:
            ET.SubElement(root, "year").text = str(self.year)

        if self.release_date:
            ET.SubElement(root, "releasedate").text = self.release_date.strftime("%Y-%m-%d")

        if self.view_count:
            ET.SubElement(root, "playcount").text = str(self.view_count)
            
        if self.duration:
            ET.SubElement(root, "runtime").text = str(int(self.duration.total_seconds()))

        if thumbnail_file_path:
            ET.SubElement(root, "thumb").text = thumbnail_file_path.name

        return root
        
    def _save_artist_nfo_file(self):
        nfo_file_path = self.artist_download_path / "artist.nfo"
        
        if nfo_file_path.exists():
            # read root from current contents
            tree = ET.parse(nfo_file_path)
            root = tree.getroot()
        else:
            # create new root
            root = ET.Element("artist")

        if root.find("name") is None:
            ET.SubElement(root, "name").text = self.artist_name

        if self.artist_description and root.find("biography") is None:
            ET.SubElement(root, "biography").text = self.artist_description

        if self.artist_audiodb_id and root.find("audiodbartistid") is None:
            ET.SubElement(root, "audiodbartistid").text = self.artist_audiodb_id

        tree = ET.ElementTree(root)
        ET.indent(tree)
        tree.write(nfo_file_path, encoding="utf-8", xml_declaration=True)

    def download(self) -> list[Path]:
        downloaded_files = super().download()

        try:
            if self.artist_thumbnail_url and not self.artist_thumbnail_path.exists():
                logger.info("Downloading Artist Art", value=self.artist_thumbnail_url)
                download_file(self.artist_thumbnail_url, self.artist_thumbnail_path)
        except Exception as e:
            logger.exception(f"Unhandled exception after downloading", value=e)
            raise

        self._save_artist_nfo_file()
    
        return downloaded_files