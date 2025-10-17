from typing import Generator
from pathlib import Path
import re

from naq_utils import custom_logging as logging
from web_video_downloader.library_item import LibraryItem
from web_video_downloader.artist import Artist
from web_video_downloader.theaudiodb import TheAudioDBAPI
from web_video_downloader.exceptions import ArtistNotFound, TrackNotFound
from web_video_downloader.utils import match_title, fetch_art

youtube_api = None


def _case_insensitive_path_exists(path: Path) -> bool:

    for item in path.parent.iterdir():
        if item.name.lower() == path.name.lower():
            return True

    return False


class Video(LibraryItem):
    def __init__(self, youtube_id: str, artist_name: str, song_title: str, full_title: str | None = None, track_info: dict | None = None):
        audiodb_info = track_info or TheAudioDBAPI.track_info(artist_name, song_title)
        super().__init__(audiodb_info)

        # handle a full URL being passed for the youtube_id
        if "v=" in youtube_id:
            youtube_id = youtube_id.split("v=")[1].split("&")[0]

        self._youtube_info: dict | None = None

        self.youtube_id = youtube_id
        self.song_title = song_title
        self.full_title = full_title or self.song_title

        self.year_released: int = 0  # use default value of 0 for sorting purposes

        self.artist = Artist(artist_name)

        self.episode_num = self._determine_episode_num()

        # self._imvdb_info = IMVDB.for_youtube_id([self.artist.name, self.song_title], self.youtube_id)

    def __repr__(self):
        return f"Video(Artist='{self.artist.name}' Title='{self.full_title}')"

    @property
    def name(self) -> str:
        return self.full_title

    @property
    def metadata(self) -> dict:
        md = super().metadata
        # if self._imvdb_info:
        #     md.update(imvdb=self._imvdb_info)
        return md

    @property
    def youtube_url(self) -> str | None:
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @classmethod
    def from_youtube_playlist_item(cls, item: dict) -> "Video | None":
        title = item["snippet"]["title"]
        match = match_title(title)

        if match:
            youtube_id = (item.get("contentDetails", {}) or item.get("id", {}))["videoId"]

            return cls(youtube_id, match.artist_name, match.song_title, full_title=match.full_song_title)
        else:
            logging.debug(f"No title match: {title}")

        return None

    @classmethod
    def from_youtube_id(cls, youtube_id: str) -> "Video | None":
        from web_video_downloader.youtube_api import YouTubeAPI
        youtube = YouTubeAPI()

        video_info = youtube.get_video_info(youtube_id)
        title = video_info["snippet"]["title"]
        match = match_title(title)

        if match:
            return cls(youtube_id, match.artist_name, match.song_title, full_title=match.full_song_title)
        else:
            logging.debug(f"No title match: {title}")
            return None

    @classmethod
    def from_found_obj_files(cls, *args, **kwargs) -> Generator["Video", None, None]:
        for library_item in super().from_found_obj_files("Video"):
            assert isinstance(library_item, Video)
            yield library_item

    @classmethod
    def for_artist(cls, artist: Artist) -> Generator["Video", None, None]:
        for video_dict in TheAudioDBAPI.mvids(artist.name):
            try:
                yield Video(video_dict["strMusicVid"], artist.name, video_dict["strTrack"])
            except TrackNotFound as e:
                logging.warning(str(e))

    # @classmethod
    # def for_artist_and_song(cls, artist_name: str, song_title: str, full_title: str = None, update_cache: bool = False) -> Optional["Video"]:
    #     track_info = TheAudioDBAPI.track_info(artist_name, song_title, update_cache=update_cache)
    #     if track_info:
    #         return Video(track_info["strMusicVid"],
    #                      track_info["strArtist"],
    #                      track_info["strTrack"],
    #                      full_title=full_title)

    # @property
    # def metadata(self) -> Dict:
    #     _metadata = {
    #         "index.value": self.episode_num,
    #         "title.value": self.full_title,
    #         "summary.value": self.info.get("strDescriptionEN") or self.info.get("strDescription") or "",
    #         "rating.value": float(self.info["intScore"]) if self.info["intScore"] else "0.0",
    #     }
    #
    #     if self.year_released:
    #         _metadata["year.value"] = self.year_released
    #
    #     # if self.youtube_info:
    #     #     _metadata.update({
    #     #         "summary.value": self.youtube_info["snippet"]["description"],
    #     #         "viewCount.value": self.youtube_info["statistics"]["viewCount"]
    #     #     })
    #
    #     return _metadata

    @property
    def youtube_info(self) -> dict:
        if not hasattr(self, "_youtube_info") or self._youtube_info is None:
            global youtube_api
            from web_video_downloader.youtube_api import YouTubeAPI
            youtube_api = youtube_api or YouTubeAPI()
            self._youtube_info = youtube_api.get_video_info(self.youtube_id) if self.youtube_id else None
        return self._youtube_info

    @property
    def view_count(self) -> int:
        return int(self.youtube_info.get("statistics", {}).get("viewCount", 0)) if self.youtube_info else 0

    @property
    def genre(self) -> str:
        return self.metadata.get("audiodb", {}).get("strGenre") or ""

    def _determine_episode_num(self) -> int:
        filename_regex = r"(\d\d)\s-\s(.+)\..+"

        # hasn't been downloaded yet. pick the next available episode number in this season
        used_episode_nums = []
        for item in self.artist.download_path.iterdir():
            match = re.match(filename_regex, item.name)
            if match is not None:
                video_episode_num, title = match.groups()
                video_episode_num = int(video_episode_num)
                if title.strip().lower() == self.full_title.strip().lower():
                    # this video has already been downloaded, just use its episode number
                    return video_episode_num
                used_episode_nums.append(video_episode_num)

        ep_num = 1
        while True:
            if ep_num not in used_episode_nums:
                return ep_num
            else:
                ep_num += 1

    @property
    def download_path(self) -> Path:
        return self.artist.download_path / self.full_title / f"{self.full_title}.mp4"

    def is_downloaded(self) -> bool:
        if not self.artist.download_path.exists():
            return False

        if not self.download_path.parent.exists():
            return False

        return _case_insensitive_path_exists(self.download_path)

    def save_nfo_file(self, downloaded_files: list[Path]):
        from xml.etree import ElementTree as ET

        if self.artist:
            self.artist.save_nfo_file()

        video_file_path = None
        for file in downloaded_files:
            if file.suffix.lower() == ".mp4":
                video_file_path = file
                break

        if video_file_path:
            logging.info(f"Writing NFO for", value=self)

            artist_info = self.artist._audiodb_info

            nfo_path = video_file_path.parent / f"{video_file_path.stem}.nfo"
            root = ET.Element("movie")

            if artist_info:
                audiodb_artist_id = ET.SubElement(root, "audiodbartistid")
                audiodb_artist_id.text = artist_info["idArtist"]

            if self._audiodb_info:
                if self._audiodb_info["strDescriptionEN"]:
                    plot_elem = ET.SubElement(root, "plot")
                    plot_elem.text = self._audiodb_info["strDescriptionEN"]

                title_elem = ET.SubElement(root, "title")
                title_elem.text = self._audiodb_info["strTrack"]

                album_info = TheAudioDBAPI().album_info(self._audiodb_info["idAlbum"])
                if album_info:
                    year_elem = ET.SubElement(root, "year")
                    year_elem.text = album_info["intYearReleased"]

            tree = ET.ElementTree(root)
            ET.indent(tree)
            tree.write(nfo_path, encoding="utf-8", xml_declaration=True)


    def download(self):
        from web_video_downloader.youtube_api import YouTubeAPI

        try:
            if self.is_downloaded():
                logging.success(f"Already downloaded, so skipping", value=self)
                return

            logging.info(f"Downloading Video", value=self)

            downloaded_files = YouTubeAPI.download(self.youtube_url, self.download_path)

            if downloaded_files:
                logging.info(f"Successfully downloaded", value=self)

                self.save_nfo_file(downloaded_files)

                if self.artist.art_url:
                    logging.info("Fetching Artist Art from", value=self.artist.art_url)
                    fetch_art(self.artist.art_url, self.artist.download_path)

                # save ourselves alongside the video for future reference
                self.save_obj_file()

                # also save our artist
                self.artist.save_obj_file()
            else:
                if self.download_path.exists():
                    self.download_path.unlink()
                logging.error("Failed to download", value=self)
        except (ArtistNotFound, TrackNotFound) as e:
            logging.info(str(e))
        except Exception as e:
            logging.exception(f"Unhandled exception while downloading", value=e)
