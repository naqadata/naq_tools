from dataclasses import dataclass
from datetime import timedelta
import re
from typing import Generator, Iterator
from xml.etree import ElementTree as ET
import json

import emoji
from pyyoutube import Video, Playlist

from naq_3p_apis.youtube_api import YouTubeAPI
from naq_3p_apis.yt_dlp import YT_DLP
from naq_utils.extensions import Path
from naq_utils.logging import logger
from naq_utils.serialize import Serialize
from naq_utils.settings import JsonFile
from naq_video_downloader.settings import GlobalSettings


class KnownPlaylists(JsonFile):
    @dataclass
    class _KnownPlaylistInfo:
        playlist_id: str
        playlist_name: str
        music_videos: bool
        download_path: Path

    class _JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, KnownPlaylists._KnownPlaylistInfo):
                return {
                    "__objecttype__": "_KnownPlaylistInfo",
                    "playlist_id": o.playlist_id,
                    "playlist_name": o.playlist_name,
                    "music_videos": o.music_videos,
                    "download_path": str(o.download_path) if o.download_path else None
                }
            return super().default(o)
        
    class _JSONDecoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            super().__init__(object_hook=self.object_hook, *args, **kwargs)

        def object_hook(self, obj, *args, **kwargs):

            if obj.get("__objecttype__") == "_KnownPlaylistInfo":
                return KnownPlaylists._KnownPlaylistInfo(
                    obj["playlist_id"],
                    obj["playlist_name"],
                    obj["music_videos"],
                    obj["download_path"]
                )

            return obj
        
    _decoder_class = _JSONDecoder
    _encoder_class = _JSONEncoder
        
    def __init__(self):
        super().__init__("known_playlists")

    def __iter__(self) -> Iterator[_KnownPlaylistInfo]:
        yield from self.iter_playlists()

    def add_playlist(self, playlist: Playlist, is_music_videos: bool, download_path: Path):
        assert playlist.id, "Playlist must have valid ID"
        assert playlist.snippet and playlist.snippet.title, "Playlist must have valid title"

        self[playlist.id] = self._KnownPlaylistInfo(playlist.id, playlist.snippet.title, is_music_videos, download_path)

        self.save()

    def iter_playlists(self) -> Generator[_KnownPlaylistInfo, None, None]:
        yield from self.values()

    def get_playlists(self) -> list[_KnownPlaylistInfo]:
        return list(self.values())


class YouTubeVideo(Serialize):
    _known_playlists: KnownPlaylists = KnownPlaylists()
    
    @dataclass
    class _YouTubeVideoIterator:
        video: "YouTubeVideo"
        index: int
        total: int

    def __init__(self, youtube_id: str, title: str):
        # handle both full YT URL or just ID
        youtube_id = youtube_id.split("v=")[1].split("&")[0] if "v=" in youtube_id else youtube_id

        self.youtube_id = youtube_id
        self._youtube_video: Video | None = None
        self.title = title

    def __repr__(self):
        return f"Video({self.youtube_id})"
    
    @staticmethod
    def youtube_api() -> YouTubeAPI:
        return YouTubeAPI(GlobalSettings().google_api_key.value)

    @classmethod
    def from_youtube_id(cls, youtube_id: str) -> "YouTubeVideo | None":
        # handle both full YT URL or just ID
        youtube_id = youtube_id.split("v=")[1].split("&")[0] if "v=" in youtube_id else youtube_id
        
        video = cls.youtube_api().get_video(youtube_id)        
        return cls(youtube_id, video.snippet.title) if video and video.snippet and video.snippet.title else None

    @classmethod
    def download_playlist(cls, youtube_playlist_id: str, is_music_videos: bool) -> list[Path]:
        downloaded_files: list[Path] = []
        playlist = cls.youtube_api().get_playlist(youtube_playlist_id)
        assert playlist, f"Failed to find playlist for YouTube ID: {youtube_playlist_id}"

        cls._known_playlists.add_playlist(playlist, is_music_videos, GlobalSettings().download_dir.value)

        for video_iter in cls.iter_youtube_playlist(youtube_playlist_id):
            logger.status(f"Playlist Video", value=video_iter.video, prefix=f"{video_iter.index} / {video_iter.total}")
            try:
                files = video_iter.video.download()
                downloaded_files.extend(files)
            except Exception as e:
                logger.exception(f"Unhandled exception while downloading video in playlist", value=e)

        return downloaded_files

    @classmethod
    def iter_known_playlists(cls, music_videos: bool = True, general_videos: bool = True) -> Generator[KnownPlaylists._KnownPlaylistInfo, None, None]:
        for playlist_info in cls._known_playlists.iter_playlists():
            if (playlist_info.music_videos and music_videos) or (not playlist_info.music_videos and general_videos):
                yield playlist_info
    
    @classmethod
    def print_known_playlists(cls, music_videos: bool = True, general_videos: bool = True):
        header = f"{'Playlist ID':<37} | {'Title':<50} | {'Music Videos':^16} | {'Download Path':<50}"
        logger.success("-" * len(header))
        logger.success(header)
        logger.success("-" * len(header))

        for playlist_info in cls.iter_known_playlists(music_videos, general_videos):
            if (playlist_info.music_videos and not music_videos) or (not playlist_info.music_videos and not general_videos):
                continue
            
            title = re.sub(r":.+:", "", emoji.demojize(playlist_info.playlist_name))
            if len(title) > 45:
                title = f"{title[:45].strip()}..."

            logger.success(f"{playlist_info.playlist_id:<37} | {title:<50} | {('X' if playlist_info.music_videos else ''):^16} | {str(playlist_info.download_path):<50}")
    
    @classmethod
    def iter_youtube_playlist(cls, youtube_playlist_id: str) -> "Generator[YouTubeVideo._YouTubeVideoIterator, None, None]":
        # handle both full YT URL or just ID
        youtube_playlist_id = youtube_playlist_id.split("list=")[1].split("&")[0] if "list=" in youtube_playlist_id else youtube_playlist_id

        api = cls.youtube_api()
        playlist = api.get_playlist(youtube_playlist_id)

        for idx, video in enumerate(api.iter_playlist_videos(youtube_playlist_id), start=1):
            if video and video.id and video.snippet and video.snippet.title:
                youtube_video = cls.from_youtube_id(video.id)
                assert youtube_video, f"Failed to create YouTubeVideo for video ID: {video.id}"

                yield cls._YouTubeVideoIterator(
                    video = youtube_video, 
                    index = idx, 
                    total = playlist.contentDetails.itemCount if playlist and playlist.contentDetails and playlist.contentDetails.itemCount else 0
                )
    
    @property
    def youtube_url(self) -> str | None:
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @property
    def youtube_video(self) -> Video | None:
        if not self._youtube_video:
            self._youtube_video = self.youtube_api().get_video(self.youtube_id) if self.youtube_id else None
        return self._youtube_video
    
    @property
    def download_path(self) -> Path:
        return GlobalSettings().download_dir.value / f"{self.title}.mp4"

    @property
    def name(self) -> str:
        return self.title

    @property
    def view_count(self) -> int:
        if self.youtube_video and self.youtube_video.statistics and self.youtube_video.statistics.viewCount is not None:
            return self.youtube_video.statistics.viewCount
        return 0
    
    @property
    def duration(self) -> timedelta | None:
        if self.youtube_video and self.youtube_video.contentDetails and self.youtube_video.contentDetails.duration:
            # regex taken from: https://gist.github.com/spatialtime/c1924a3b178b4fe721fe406e0bf1a1dc
            m = re.match(r'^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:.\d+)?)S)?$', self.youtube_video.contentDetails.duration)
                        
            return timedelta(
                days = int(m[3]) if m[3] else 0,
                hours = int(m[4]) if m[4] else 0,
                minutes = int(m[5]) if m[5] else 0,
                seconds = float(m[6]) if m[6] else 0
            ) if m else None

    @property
    def downloaded(self) -> bool:        
        return self.download_path.exists()
    
    def _get_nfo_xml_root(self, video_file_path: Path, thumbnail_file_path: Path | None = None) -> ET.Element:
        logger.info(f"Writing NFO for", value=self)

        root = ET.Element("movie")

        if video_file_path:            
            ET.SubElement(root, "title").text = self.title

            if self.view_count:
                ET.SubElement(root, "playcount").text = str(self.view_count)
                
            if self.duration:
                ET.SubElement(root, "runtime").text = str(int(self.duration.total_seconds()))

            if thumbnail_file_path:
                ET.SubElement(root, "thumb").text = thumbnail_file_path.name

        return root

    def _save_nfo_file(self, downloaded_files: list[Path]) -> Path | None:
        video_file_path = None
        thumbnail_file_path = None

        for file in downloaded_files:
            if file.suffix.lower() == ".mp4":
                video_file_path = file
            elif file.suffix.lower() == ".jpg":
                thumbnail_file_path = file

        if video_file_path:
            nfo_file_path = video_file_path.parent / f"{video_file_path.stem}.nfo"

            root = self._get_nfo_xml_root(video_file_path, thumbnail_file_path)
            tree = ET.ElementTree(root)
            ET.indent(tree)
            tree.write(nfo_file_path, encoding="utf-8", xml_declaration=True)

            return nfo_file_path

    def download(self) -> list[Path]:
        assert self.youtube_url

        try:
            if self.downloaded:
                logger.success(f"Already downloaded", value=self)
                return []

            logger.info(f"Downloading", value=self)

            downloaded_files = YT_DLP.download(self.youtube_url, self.download_path)

            if downloaded_files:
                logger.success(f"Downloaded", value=self)

                nfo_path = self._save_nfo_file(downloaded_files)
                if nfo_path:
                    downloaded_files.append(nfo_path)

                # TODO: cache ourselves on disk
                # self.save_obj_file()
            else:
                if self.download_path.exists():
                    self.download_path.unlink()
                logger.error("Failed to download", value=self)

            return downloaded_files
        except Exception as e:
            logger.exception(f"Unhandled exception while downloading", value=e)
            raise