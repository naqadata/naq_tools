import argparse
import os
import re
import shutil
import subprocess
import sys

import emoji
from pyyoutube import Video

from naq_utils.extensions import Path
from naq_utils.logging import logger
from naq_utils.naq_tool import NaqTool
from naq_video_downloader.settings import GlobalSettings
from naq_video_downloader.youtube_video import YouTubeVideo
from naq_video_downloader.youtube_music_video import MusicVideo


DEFAULT_DOWNLOAD_MIN_VIEW_COUNT = 50 * 1000 * 1000


class DownloaderTool(NaqTool):
    def _populate_parser(self):
        self.parser.add_argument("--interactive", default=False, action="store_true",
                                 help="Ask user for clarification when songs are not matched")
        self.parser.add_argument("--permissive", default=False, action="store_true", 
                                 help="Do not apply strict name policies to music videos from YouTube")
        self.parser.add_argument("--audiodb-api-key", default=os.environ.get("AUDIODB_API_KEY"), 
                                 help="API Key for use with theaudiodb API. Overrides AUDIODB_API_KEY env var, if specified. Default: %(default)s")
        self.parser.add_argument("--imvdb-api-key", default=os.environ.get("IMVDB_API_KEY"), 
                                 help="API Key for use with IMVDB API. Overrides IMVDB_API_KEY env var, if specified. Default: %(default)s")
        self.parser.add_argument("--google-api-key", default=os.environ.get("GOOGLE_API_KEY"), 
                                 help="API Key for use with Google API. Overrides GOOGLE_API_KEY env var, if specified. Default: %(default)s")

        subparsers = self.parser.add_subparsers(dest='command')

        # YOUTUBE DOWNLOAD
        # Get download dir either from bazel environment (BUILD_WORKING_DIRECTORY) or resort to CWD
        default_download_dir = Path(os.environ.get("BUILD_WORKING_DIRECTORY") or Path.cwd().absolute())

        youtube_download_parser = subparsers.add_parser("download", help="Download from YouTube")
        youtube_download_parser.add_argument("--download-dir", type=Path, default=default_download_dir,
                                             help='Where downloads should be stored. Default: %(default)s')
        youtube_download_parser.add_argument("--min-view-count", type=int, default=DEFAULT_DOWNLOAD_MIN_VIEW_COUNT,
                                 help="Downloads are skipped if the view count is below this threshold. Default: %(default)s")
        
        download_subparsers = youtube_download_parser.add_subparsers(dest="download_subcommand")

        target_download_parser = download_subparsers.add_parser("targets", help="Download by YouTube ID(s) or URL(s)")
        target_download_parser.add_argument("targets", nargs="*", help="Include specified Playlist or Video. Can be YouTube ID(s) or a URL(s).")
        target_download_parser.add_argument("--music-videos", default=False, action="store_true", 
                                            help="Should the video(s)/playlist(s) be treated as music videos? Will attempt to match Artist, etc.")
        
        moe_download_parser = download_subparsers.add_parser("more-of-everything", help="Download more music videos for all the artists already downloaded. (Music Videos only)")
        # moe_download_parser.add_argument("--search-engine", choices=["audiodb", "youtube"], default="audiodb", help="YT is limited to 100 artist queries per day, at most. Default: %(default)s")

        yt_search_parser = download_subparsers.add_parser("youtube_search", help="Search YouTube with given query. Matching videos will be downloaded")
        yt_search_parser.add_argument("youtube_search_query", help="Search query to use on YouTube")

        # KNOWN YOUTUBE PLAYLISTS
        playlist_parser = subparsers.add_parser("playlists", help="Operations with known playlists, downloaded previously")
        playlist_parser.add_argument("playlist_subcommand", choices=["list", "refresh"], help="Subcommand for playlist operations")
        playlist_parser.add_argument("--playlist-type", choices=["music-video", "general", "all"], default="all",
                                    help="music-video: playlists of music videos; general: playlists of general videos (non-music-video); all: playlists of both types. Default: %(default)s")

        subparsers.add_parser("prune", help="Prune any empty artist directories")

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

    def main(self, args: argparse.Namespace):
        GlobalSettings().interactive.value = args.interactive
        GlobalSettings().permissive.value = args.permissive
        GlobalSettings().audiodb_api_key.value = args.audiodb_api_key
        GlobalSettings().google_api_key.value = args.google_api_key
        GlobalSettings().imvdb_api_key.value = args.imvdb_api_key

        if not args.audiodb_api_key:
            raise RuntimeError("Must specify an API key to use with TheAudioDB API. Use cmd line or AUDIODB_API_KEY env var")
        
        if not args.google_api_key:
            raise RuntimeError("Must specify an API key to use with Google API. Use cmd line or GOOGLE_API_KEY env var")

        try:
            if args.command == "download":
                GlobalSettings().download_dir.value = args.download_dir
                GlobalSettings().min_view_count.value = args.min_view_count

                if args.download_subcommand == "targets":

                    video_class = MusicVideo if args.music_videos else YouTubeVideo
                    
                    for youtube_id in args.targets or []:
                        video = video_class.from_youtube_id(youtube_id)
                        if video:
                            # target ID matched a single video, so download it
                            video.download()
                        else:
                            # try as playlist
                            video_class.download_playlist(youtube_id, args.music_videos)

                elif args.download_subcommand == "more-of-everything":
                    # Scan the artists in the download dir
                    for video in MusicVideo.audiodb_search_for_more():
                        video.download()

                elif args.download_subcommand == "youtube_search":
                    for video in MusicVideo.youtube_search(args.youtube_search_query):
                        video.download()

                self._delete_empty_artist_dirs()

            elif args.command == "playlists":
                music_videos = args.playlist_type in ["music-video", "all"]
                general_videos = args.playlist_type in ["general", "all"]

                if args.playlist_subcommand == "list":
                    YouTubeVideo.print_known_playlists(music_videos=music_videos, general_videos=general_videos)
                elif args.playlist_subcommand == "refresh":
                    for known_playlist in YouTubeVideo.iter_known_playlists(music_videos=music_videos, general_videos=general_videos):
                        logger.status(f"Refreshing known playlist", value=known_playlist.playlist_name)
                        video_class = MusicVideo if known_playlist.music_videos else YouTubeVideo
                        
                        GlobalSettings().download_dir.value = Path(known_playlist.download_path)
                        video_class.download_playlist(known_playlist.playlist_id, known_playlist.music_videos)

                self._delete_empty_artist_dirs()

            elif args.command == "prune":
                self._delete_empty_artist_dirs()
                self._remove_duplicate_videos()

            else:
                raise ValueError(f"Invalid command: {args.command}")

        except KeyboardInterrupt:
            print("")


def main():
    parser = argparse.ArgumentParser(description="Web Video Downloader Tool")
    tool = DownloaderTool(parser)

    parser.add_argument("--log-level", choices=["debug", "info", "status", "warning", "error"], default="info", help="Set logging level. Default: %(default)s")
    
    args = parser.parse_args()

    import logging
    logger.setLevel(level=getattr(logging, args.log_level.upper()))

    tool.main(args)


if __name__ == "__main__":    
    main()
