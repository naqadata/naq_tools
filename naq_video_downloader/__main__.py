import argparse
import logging
import os
import shutil
import sys

from naq_3p_apis.yt_dlp import YT_DLP
from naq_utils.extensions import Path
from naq_utils.logging import logger
from naq_utils.naq_tool import NaqTool
from naq_video_downloader.settings import GlobalSettings
from naq_video_downloader.youtube_music_video import MusicVideo
from naq_video_downloader.youtube_video import YouTubeVideo


DEFAULT_DOWNLOAD_MIN_VIEW_COUNT = 50 * 1000 * 1000


def _parse_args(parser: argparse.ArgumentParser, argv: list[str] | None = None) -> argparse.Namespace:
    """Parse downloader arguments, retaining tokens after ``--`` for yt-dlp."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        separator_index = argv.index("--")
    except ValueError:
        downloader_args, yt_dlp_args = argv, []
    else:
        downloader_args, yt_dlp_args = argv[:separator_index], argv[separator_index + 1:]

    args = parser.parse_args(downloader_args)
    args.yt_dlp_args = yt_dlp_args
    return args


class DownloaderTool(NaqTool):
    def _populate_parser(self):
        music_options = self.parser.add_argument_group("music-video options")
        music_options.add_argument(
            "--interactive",
            action="store_true",
            help="Ask for artist and title when a music-video title is not recognized.",
        )
        music_options.add_argument(
            "--permissive",
            action="store_true",
            help="Use more relaxed music-video title matching.",
        )
        music_options.add_argument(
            "--audiodb-api-key",
            default=os.environ.get("AUDIODB_API_KEY"),
            help="API key for TheAudioDB. Overrides AUDIODB_API_KEY when supplied.",
        )
        music_options.add_argument(
            "--imvdb-api-key",
            default=os.environ.get("IMVDB_API_KEY"),
            help="API key for IMVDB. Overrides IMVDB_API_KEY when supplied.",
        )
        music_options.add_argument(
            "--google-api-key",
            default=os.environ.get("GOOGLE_API_KEY"),
            help="API key for YouTube Data API. Overrides GOOGLE_API_KEY when supplied.",
        )

        subparsers = self.parser.add_subparsers(dest="command", required=True)
        default_download_dir = Path.cwd().absolute()

        def add_download_dir(parser: argparse.ArgumentParser) -> None:
            parser.add_argument(
                "--download-dir",
                type=Path,
                default=default_download_dir,
                help="Directory for downloaded files. Default: %(default)s",
            )

        video_parser = subparsers.add_parser(
            "video",
            aliases=["download"],
            help="Download one or more YouTube videos or playlists.",
        )
        add_download_dir(video_parser)
        video_parser.add_argument(
            "--min-view-count",
            type=int,
            default=DEFAULT_DOWNLOAD_MIN_VIEW_COUNT,
            help="Skip videos below this view count. Default: %(default)s",
        )
        video_parser.add_argument(
            "--music-video",
            action="store_true",
            help="Fetch artist metadata and organize each target as a music video.",
        )
        video_parser.add_argument("targets", nargs="+", help="YouTube video IDs, video URLs, or playlist URLs.")

        album_parser = subparsers.add_parser(
            "album",
            help="Split a chaptered album video into separate MP4 tracks.",
        )
        add_download_dir(album_parser)
        album_parser.add_argument("targets", nargs="+", help="YouTube URLs or IDs for chaptered album videos.")

        audio_album_parser = subparsers.add_parser(
            "audio-album",
            help="Download a chaptered album video as separate MP3 tracks.",
        )
        add_download_dir(audio_album_parser)
        audio_album_parser.add_argument("targets", nargs="+", help="YouTube URLs or IDs for chaptered album videos.")
        audio_album_parser.add_argument("--artist", required=True, help="Contributing artist to embed in each MP3.")
        audio_album_parser.add_argument("--album", required=True, help="Album title to embed in each MP3.")

        more_parser = subparsers.add_parser(
            "more",
            aliases=["more-of-everything"],
            help="Download more music videos for artists already in the library.",
        )
        add_download_dir(more_parser)

        search_parser = subparsers.add_parser("search", help="Find and download music videos from a YouTube search.")
        add_download_dir(search_parser)
        search_parser.add_argument("query", help="YouTube search query.")

        playlist_parser = subparsers.add_parser(
            "playlist",
            aliases=["playlists"],
            help="List or refresh previously downloaded playlists.",
        )
        playlist_parser.add_argument("action", choices=["list", "refresh"], help="Operation to perform.")
        playlist_parser.add_argument(
            "--playlist-type",
            choices=["music-video", "general", "all"],
            default="all",
            help="Which saved playlists to use. Default: %(default)s",
        )

        subparsers.add_parser("prune", help="Remove empty artist directories and duplicate video folders.")

    @staticmethod
    def _delete_empty_artist_dirs():
        for item in Path.cwd().iterdir():
            if item.is_dir() and not any(item.iterdir()):
                logger.status("Deleting empty directory", value=item)
                item.rmdir()

    @staticmethod
    def _remove_duplicate_videos():
        already_seen = set()
        duplicates = []

        for artist_path in Path.cwd().iterdir():
            for video_dir_path in artist_path.iterdir():
                if video_dir_path.is_dir():
                    key = f"{artist_path.name.lower()}/{video_dir_path.name.lower()}"
                    if key in already_seen:
                        duplicates.append(video_dir_path)
                    else:
                        already_seen.add(key)

        for duplicate in duplicates:
            logger.status("Removing duplicate video", value=duplicate)
            shutil.rmtree(duplicate)

    @staticmethod
    def _require_api_keys(args: argparse.Namespace, *key_names: str) -> None:
        keys = {
            "TheAudioDB": args.audiodb_api_key,
            "IMVDB": args.imvdb_api_key,
            "YouTube Data API": args.google_api_key,
        }
        missing = [name for name in key_names if not keys[name]]
        if missing:
            raise RuntimeError(f"Missing API key(s): {', '.join(missing)}")

    def main(self, args: argparse.Namespace):
        YT_DLP.extra_args = tuple(getattr(args, "yt_dlp_args", ()))
        GlobalSettings().interactive.value = args.interactive
        GlobalSettings().permissive.value = args.permissive
        GlobalSettings().audiodb_api_key.value = args.audiodb_api_key
        GlobalSettings().google_api_key.value = args.google_api_key
        GlobalSettings().imvdb_api_key.value = args.imvdb_api_key

        if args.command in {"album", "audio-album"}:
            GlobalSettings().download_dir.value = args.download_dir
            for target in args.targets:
                if args.command == "audio-album":
                    logger.status("Downloading chaptered audio album", value=target)
                    YT_DLP.download_audio_chapters(
                        target,
                        args.download_dir,
                        artist=args.artist,
                        album=args.album,
                    )
                else:
                    logger.status("Downloading chaptered album", value=target)
                    YT_DLP.download_chapters(target, args.download_dir)
            return

        try:
            if args.command in {"video", "download"}:
                self._require_api_keys(args, "YouTube Data API")
                GlobalSettings().download_dir.value = args.download_dir
                GlobalSettings().min_view_count.value = args.min_view_count
                if args.music_video:
                    self._require_api_keys(args, "TheAudioDB", "IMVDB")

                video_class = MusicVideo if args.music_video else YouTubeVideo
                for youtube_id in args.targets:
                    video = video_class.from_youtube_id(youtube_id)
                    if video:
                        video.download()
                    else:
                        video_class.download_playlist(youtube_id, args.music_video)
                self._delete_empty_artist_dirs()

            elif args.command in {"more", "more-of-everything"}:
                self._require_api_keys(args, "TheAudioDB", "IMVDB", "YouTube Data API")
                GlobalSettings().download_dir.value = args.download_dir
                for video in MusicVideo.audiodb_search_for_more():
                    video.download()
                self._delete_empty_artist_dirs()

            elif args.command == "search":
                self._require_api_keys(args, "TheAudioDB", "IMVDB", "YouTube Data API")
                GlobalSettings().download_dir.value = args.download_dir
                for video in MusicVideo.youtube_search(args.query):
                    video.download()
                self._delete_empty_artist_dirs()

            elif args.command in {"playlist", "playlists"}:
                music_videos = args.playlist_type in ["music-video", "all"]
                general_videos = args.playlist_type in ["general", "all"]

                if args.action == "list":
                    YouTubeVideo.print_known_playlists(music_videos=music_videos, general_videos=general_videos)
                elif args.action == "refresh":
                    self._require_api_keys(args, "YouTube Data API")
                    if music_videos:
                        self._require_api_keys(args, "TheAudioDB", "IMVDB")
                    for known_playlist in YouTubeVideo.iter_known_playlists(
                        music_videos=music_videos,
                        general_videos=general_videos,
                    ):
                        logger.status("Refreshing known playlist", value=known_playlist.playlist_name)
                        video_class = MusicVideo if known_playlist.music_videos else YouTubeVideo
                        GlobalSettings().download_dir.value = Path(known_playlist.download_path)
                        video_class.download_playlist(known_playlist.playlist_id, known_playlist.music_videos)

                self._delete_empty_artist_dirs()

            elif args.command == "prune":
                self._delete_empty_artist_dirs()
                self._remove_duplicate_videos()

        except KeyboardInterrupt:
            print("")


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Download YouTube videos, chaptered audio albums, and music-video libraries.")
    tool = DownloaderTool(parser)
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "status", "warning", "error"],
        default="info",
        help="Set logging level. Default: %(default)s",
    )

    args = _parse_args(parser, argv)
    logger.setLevel(level=getattr(logging, args.log_level.upper()))
    tool.main(args)


if __name__ == "__main__":
    main()
