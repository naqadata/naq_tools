import shutil
import tempfile
from dataclasses import dataclass
from googleapiclient.discovery import build
from typing import Generator, Dict, Optional, List, Tuple
from pathlib import Path
from naq_utils.custom_logging import logger
from naq_video_downloader.video import Video
from naq_video_downloader.utils import SettingsFile, RequestCache, GlobalSettings, fetch_art
from naq_video_downloader.exceptions import SkipVideo, TrackNotFound, ArtistNotFound
from collections import namedtuple
import re
import subprocess

DEFAULT_MAX_SEARCH_RESULTS = 50
DEFAULT_DOWNLOAD_MIN_VIEW_COUNT = 50 * 1000 * 1000

class YoutubeAPISettings(SettingsFile):
    PlaylistDownloadInfo = namedtuple("PlaylistDownload", ["download_path", "music_videos"])

    def __init__(self):
        super().__init__(".youtube_api")
        self.known_playlists: Dict[str, Dict] = self.settings.get("known_playlists", {})

    def get_playlist_info(self, playlist_id: str) -> Optional[Dict]:
        return self.settings.get("known_playlists", {}).get(playlist_id)

    def save_playlist_info(self, playlist_id: str, playlist_info: Dict) -> None:
        self.settings.setdefault("known_playlists", {})[playlist_id] = playlist_info
        self.save()

    def get_playlist_download_info(self, playlist_id: str) -> Optional[PlaylistDownloadInfo]:
        entry = self.settings.get("playlist_downloads", {}).get(playlist_id)
        if entry:
            return self.PlaylistDownloadInfo(Path(entry["download_path"]), entry["music_videos"])

    def record_playlist_download(self, playlist_id: str, download_info: PlaylistDownloadInfo):
        self.settings.setdefault("playlist_downloads", {})[playlist_id] = {
            "download_path": str(download_info.download_path),
            "music_videos": download_info.music_videos
        }
        self.save()

    @property
    def known_playlist_ids(self) -> List[str]:
        return list(self.settings.get("known_playlists", {}).keys())


class YouTubeAPI:
    DOWNLOADER_PATH = Path(__file__).parent.absolute() / "yt-dlp"

    def __init__(self):
        self._youtube = None
        self._request_cache = RequestCache("youtube-api")
        self._settings_file = YoutubeAPISettings()

    @property
    def youtube(self):
        if not self._youtube:
            self._youtube = build(serviceName="youtube", version="v3", developerKey=GlobalSettings().google_api_key)
        return self._youtube

    @classmethod
    def download(cls, youtube_url: str, download_path: Path | None = None, file_title: str | None = None, gen_subs: bool = False) -> list[Path]:
        """
        Downloads a YouTube video and optionally generates subtitles for it. The method
        uses a specific downloader tool (referenced by a class attribute) to handle the
        video downloading process. The downloaded video can be saved to a specific file
        path or defaults to the current directory. Video thumbnails are also retrieved
        and converted to JPG format. Subtitles can be generated post-download if
        enabled.

        :param youtube_url: A string containing the URL of the YouTube video to
            download.
        :param download_path: An optional pathlib.Path object specifying the directory
            and filename where the downloaded file should be saved. If not provided,
            defaults to using the current directory.
        :param file_title: An optional string used to specify the title of the
            downloaded file.
        :param gen_subs: An optional boolean indicating whether subtitles should be
            generated for the downloaded video.
        :return: A list of pathlib.Path objects representing the downloaded file(s).
        """
        if "t=" in youtube_url:
            logger.warning(f"WTF, a timestamp is in this URL: {youtube_url}")

        cmd = [
            cls.DOWNLOADER_PATH,
            # "-f", "mp4+m4a",  # best video and audio available in mp4 format
            "-f", "bestvideo+bestaudio/best",
            # "-S", "res,ext:mp4:m4a",
            "--recode", "mp4",
            "--merge-output-format", "mp4",
            "--output", download_path.name if download_path else "%(title)s",
            "--write-thumbnail",  # save the thumbnail for the video
            "--convert-thumbnails", "jpg",  # and convert it to JPG (default is .webp)x
            "--write-subs",  # also save subtitles for the video
            # "--sub-lang", "en",  # accept only english subtitles
            "--quiet",
            "--progress", "--no-warnings",
            "--concurrent-fragments", "5",
            "--cookies-from-browser", "firefox",
            youtube_url
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            logger.info(f"Downloading video to temp dir", value=tmpdir)
            completed_proc = subprocess.run(cmd, cwd=tmpdir)

            download_dir = download_path.parent if download_path else Path.cwd()
            download_dir.mkdir(parents=True, exist_ok=True)

            # if we are generating subtitles, and if we gave gen-subs in our environment...
            if gen_subs and shutil.which("gen-subs"):
                logger.status(f"Generating subtitles for downloaded video")
                subprocess.run(["gen-subs", "."], cwd=tmpdir)

            downloaded_file_paths = []

            if completed_proc.returncode == 0:
                for downloaded_file in tmpdir.iterdir():
                    new_path = download_dir / downloaded_file.name
                    if new_path.exists():
                        new_path.unlink()
                    shutil.move(downloaded_file, new_path)
                    downloaded_file_paths.append(new_path)

            return downloaded_file_paths

    @classmethod
    def download_from_queue(cls, queue_file_path: Path):
        if not queue_file_path.exists():
            return

        @dataclass
        class QueueEntry:
            url: str
            downloaded: bool

        class QueueFile:
            def __init__(self):
                self.queue: List[QueueEntry] = []

                self.reload()

            def reload(self):
                self.queue.clear()
                with queue_file_path.open("r") as f:
                    for line in f:
                        downloaded = line.startswith("DONE - ")
                        url = line.replace("DONE - ", "").strip()
                        self.queue.append(QueueEntry(url, downloaded))

            def save(self):
                with queue_file_path.open("w") as f:
                    for entry in self.queue:
                        line = f"DONE - {entry.url}" if entry.downloaded else entry.url
                        f.write(f"{line}\n")

            def get_next(self) -> Optional[str]:
                for entry in self.queue:
                    if not entry.downloaded:
                        return entry.url

            def mark_downloaded(self, url: str):
                for entry in self.queue:
                    if entry.url == url:
                        entry.downloaded = True
                        self.save()

        queue_file = QueueFile()
        next_download_url = queue_file.get_next()
        if next_download_url:
            logger.status("Downloading next item from queue", value=next_download_url)
            if cls.download(next_download_url):
                queue_file.mark_downloaded(next_download_url)

    @classmethod
    def download_item(cls, item: Dict, show_path: Path) -> bool:
        title = re.sub(r"/", "-", item["snippet"]["title"])
        video_id = (item.get("contentDetails", {}) or item.get("id", {}))["videoId"]
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        download_path = show_path / f"{title}.mp4"

        if download_path.exists():
            logger.debug(f"Already downloaded", value=download_path)
            return True

        logger.status(f"Downloading", value=title)
        return cls.download(youtube_url, download_path, file_title=title)

    def download_playlist(self, playlist_id: str):
        playlist_info = self.get_playlist_info(playlist_id)

        download_info = self._settings_file.get_playlist_download_info(playlist_id)
        if download_info:
            show_path = download_info.download_path
        else:
            show_name = input(f"Collection name (or Enter for '{playlist_info['title']}'): ") or playlist_info['title']
            show_path = GlobalSettings().download_dir / show_name

        self._settings_file.record_playlist_download(playlist_id, YoutubeAPISettings.PlaylistDownloadInfo(show_path, False))

        thumbnails = playlist_info["thumbnails"]
        thumbnail = thumbnails.get("maxres") or thumbnails.get("standard") or thumbnails.get("high") or thumbnails.get("default")

        fetch_art(thumbnail["url"], show_path)

        GlobalSettings().print_index = 1
        for idx, item in enumerate(self.get_playlist_items(playlist_id, playlist_info=playlist_info)):
            self.download_item(item, show_path)

    def download_music_video_playlist(self, playlist_id: str):
        self._settings_file.record_playlist_download(playlist_id, YoutubeAPISettings.PlaylistDownloadInfo(GlobalSettings().download_dir, True))
        for idx, video in enumerate(self.get_playlist_videos(playlist_id)):
            prefix = f"{idx + 1}"

            if video.view_count < GlobalSettings().min_view_count:
                logger.warning(f"Skipping video with {video.view_count} views", value=video, prefix=prefix)
            elif video.is_downloaded():
                logger.success(f"Already downloaded, so skipping", value=video , prefix=prefix)
            else:
                logger.status(f"Downloading", value=video, prefix=prefix)
                video.download()

    def get_video_info(self, video_id: str) -> Optional[Dict]:
        response = self._request_cache.get_response(f"VIDEO-STATS-{video_id}") or self.youtube.videos().list(part="id,snippet,statistics", id=video_id).execute()

        self._request_cache.cache_response(f"VIDEO-STATS-{video_id}", response)

        video_info = response['items'][0] if response['items'] else None
        return video_info

    def get_playlist_info(self, playlist_id: str, skip_cache: bool = False) -> Dict:
        # check out known playlists first
        playlist_info = self._settings_file.get_playlist_info(playlist_id)
        if playlist_info:
            return playlist_info

        playlists = set(self._settings_file.settings.setdefault("playlists", []))
        playlists.add(playlist_id)

        response = self._request_cache.get_response(f"PL-{playlist_id}") if not skip_cache else None

        if response is None:
            yt_playlist = self.youtube.playlists()
            request = yt_playlist.list(
                part="id,snippet",
                id=playlist_id
            )

            response = request.execute()
            self._request_cache.cache_response(f"PL-{playlist_id}", response)
        else:
            logger.success(f"Using cached response for playlist", value=playlist_id)

        playlist_info = response['items'][0]['snippet']
        self._settings_file.save_playlist_info(playlist_id, playlist_info)
        return playlist_info

    def get_playlist_infos(self) -> Dict[str, Dict]:
        playlist_ids = self._settings_file.known_playlist_ids
        return {playlist_id: self._settings_file.get_playlist_info(playlist_id) for playlist_id in playlist_ids}

    def get_downloaded_playlists(self) -> List[Tuple[str, YoutubeAPISettings.PlaylistDownloadInfo, Dict]]:
        playlist_ids = self._settings_file.known_playlist_ids
        playlists = []

        for playlist_id in playlist_ids:
            playlist_info = self.get_playlist_info(playlist_id)
            download_info = self._settings_file.get_playlist_download_info(playlist_id)
            if playlist_info and download_info:
                playlists.append((playlist_id, download_info, playlist_info))

        playlists.sort(key=lambda x: (not x[1].music_videos, x[2]["title"].lower()))

        return playlists

    def get_playlist_download_info(self, playlist_id: str) -> Optional[YoutubeAPISettings.PlaylistDownloadInfo]:
        return self._settings_file.get_playlist_download_info(playlist_id)

    def get_playlist_items(self, playlist_id: str, playlist_info: Dict = None) -> Generator[Dict, None, None]:
        playlist_info = playlist_info or self.get_playlist_info(playlist_id)

        item_responses = []

        yt_playlist_items = self.youtube.playlistItems()

        request = yt_playlist_items.list(
            part="id,snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )

        while request is not None:
            try:
                response = request.execute()
            except TimeoutError:
                continue
            else:
                item_responses.append(response)
                request = yt_playlist_items.list_next(request, response)

        logger.status(f"Yielding videos from playlist", value=playlist_info["title"])

        for response in item_responses:
            for item in response['items']:
                yield item

    def get_playlist_videos(self, playlist_id: str) -> Generator[Video, None, None]:
        for item in self.get_playlist_items(playlist_id):
            try:
                video = Video.from_youtube_playlist_item(item)
                if video:
                    yield video
            except (ArtistNotFound, TrackNotFound, SkipVideo) as e:
                logger.info(str(e))

    def search(self, query: str) -> Generator[Video, None, None]:
        response = self._request_cache.get_response(f"SEARCH-{query}")
        if response is None:
            yt_search = self.youtube.search()
            request = yt_search.list(
                part="id,snippet",
                maxResults=50,
                q=query,
                type="video"
            )

            response = request.execute()
            self._request_cache.cache_response(f"SEARCH-{query}", response)

        for item in response["items"]:
            try:
                video = Video.from_youtube_playlist_item(item)
                if video and video.view_count >= GlobalSettings().min_view_count:
                    yield video
                else:
                    logger.warning(f"Skipping video with {video.view_count} views", value=video)
            except (ArtistNotFound, TrackNotFound, SkipVideo) as e:
                logger.info(str(e))
