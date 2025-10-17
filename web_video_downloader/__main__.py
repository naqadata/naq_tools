import argparse
import time

from naq_utils import console
from naq_utils import custom_logging as logging
from naq_utils.naq_tool import NaqTool
from web_video_downloader.youtube_api import YouTubeAPI, SkipVideo, DEFAULT_DOWNLOAD_MIN_VIEW_COUNT
from web_video_downloader.plex import Plex
from web_video_downloader.utils import GlobalSettings
from web_video_downloader.video import Video
from pathlib import Path
import subprocess
import shutil
import emoji
import re
import sys


class DownloaderTool(NaqTool):
    
    def _populate_parser(self):
        self.parser.add_argument("--interactive", default=False, action="store_true")
        self.parser.add_argument("--permissive", default=False, action="store_true")
        self.parser.add_argument("--min-view-count", type=int, default=DEFAULT_DOWNLOAD_MIN_VIEW_COUNT)
        self.parser.add_argument("--download-dir", type=Path, default=Path.cwd(),
                                    help='Where downloads should be stored. Default: %(default)s')
        self.parser.add_argument("--log-level", choices=['debug', 'info', 'status', 'warning', 'error', 'critical'],
                            default="status", help='Logging level. Default: %(default)s')

        subparsers = self.parser.add_subparsers(dest='command')

        # YOUTUBE DOWNLOAD
        youtube_download_parser = subparsers.add_parser("download", help="Download a single video from YouTube")
        youtube_download_parser.add_argument("youtube_id")
        youtube_download_parser.add_argument("--music-video", default=False, action="store_true")

        # YOUTUBE PLAYLISTS
        youtube_playlist_parser = subparsers.add_parser("download-playlist", help='Download all videos from a YouTube playlist')
        youtube_playlist_parser.add_argument("playlist_ids", nargs="*", help="Playlist ID")
        youtube_playlist_parser.add_argument("--music-videos", default=False, action="store_true", help="Process as Music Videos, with artist info, etc")

        # DOWNLOAD QUEUE
        download_queue_parser = subparsers.add_parser("download-queue", help="Download next item from the given queue file")
        download_queue_parser.add_argument("queue_file_path", type=Path, help="Queue file path")
        download_queue_parser.add_argument("--loop-interval", type=int, default=0, help="Seconds before downloading next item. Default is to exit after one download")

        # YOUTUBE LIST KNOWN PLAYLISTS
        subparsers.add_parser("list-playlists", help="List known (previously downloaded) YouTube playlists and exit")

        # YOUTUBE REFRESH ALL KNOWN PLAYLISTS
        refresh_parser = subparsers.add_parser("refresh-playlists", help="Download any new videos from previously downloaded playlists")
        refresh_parser.add_argument("--playlist-type", choices=["music-video", "general", "all"], default="all",
                                    help="music-video: playlists of music videos; general: playlists of general videos; all: playlists of both types. Default: %(default)s")

        # YOUTUBE SEARCH
        youtube_search_parser = subparsers.add_parser("search", help="Search YouTube and download matching videos. Note: uses a lot of your Google API quota")
        youtube_search_parser.add_argument("youtube_search_query", help="Search query")

        # UPDATE PLEX
        update_plex_parser = subparsers.add_parser("update-plex", help="Update your Plex library by scanning files for Aritst/Track information. Mostly for music videos")
        update_plex_parser.add_argument("library_name", help="Name of the library, as it exists in Plex")
        update_plex_parser.add_argument("--update-cache-for-artist", required=False, help="Name of artist whose cache data should be udpated")

        # CLEANUP PLEX
        cleanup_plex_parser = subparsers.add_parser("cleanup-plex", help="Cleanup your Plex library")
        cleanup_plex_parser.add_argument("library_name", help="Name of the library, as it exists in Plex")

        moe_parser = subparsers.add_parser('moe', help="Download more music videos for all the artists already downloaded")
        moe_parser.add_argument("--reprocess", default=False, action="store_true", help="Reprocess all artists, even if they've already been processed before")
        moe_parser.add_argument("--clear-cache", default=False, action="store_true", help="Clear cache first. Will re-process all artists!")
        moe_parser.add_argument("--search-engine", choices=["audiodb", "youtube"], default="audiodb", help="YT is limited to 100 artist queries per day, at most. Default: %(default)s")

        # REPROCESS LIBRARY - CAREFUL!
        reprocess_parser = subparsers.add_parser("reprocess")
        reprocess_parser.add_argument("--dryrun", default=False, action="store_true")

        subparsers.add_parser("prune", help="Prune any empty artist directories")

        subparsers.add_parser("analyze")

    def main(self):
        args = self.parser.parse_args()

        logging.init(getattr(logging, args.log_level.upper()))

        GlobalSettings().download_dir = args.download_dir
        GlobalSettings().interactive = args.interactive
        GlobalSettings().permissive = args.permissive
        GlobalSettings().min_view_count = args.min_view_count

        def _delete_empty_artist_dirs():
            for item in Path.cwd().iterdir():
                if item.is_dir() and not any(item.iterdir()):
                    logging.status("Deleting empty directory", value=item)
                    item.rmdir()

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
                logging.status("Removing duplicate video", value=duplicate)
                shutil.rmtree(duplicate)

        try:
            if args.command == "download":
                if args.music_video:
                    video = Video.from_youtube_id(args.youtube_id)
                    if video:
                        video.download()
                else:
                    YouTubeAPI.download(args.youtube_url)

            elif args.command == "download-queue":
                queue_file_path = args.queue_file_path

                while True:
                    YouTubeAPI.download_from_queue(queue_file_path)

                    if args.loop_interval == 0:
                        break

                    logging.status(f"Waiting {args.loop_interval} seconds before downloading next item")
                    time.sleep(args.loop_interval)

            elif args.command == "list-playlists":
                header = f"{'Playlist ID':<37} | {'Title':<50} | {'Music Videos':^16} | {'Download Path':<50}"
                console.print_success("-" * len(header) + f"\n{header}\n" + "-" * len(header))
                youtube = YouTubeAPI()

                for playlist_id, download_info, playlist_info in youtube.get_downloaded_playlists():
                    title = re.sub(r":.+:", "", emoji.demojize(playlist_info['title']))
                    if len(title) > 45:
                        title = f"{title[:45].strip()}..."

                    download_info = youtube.get_playlist_download_info(playlist_id)
                    sys.stdout.write(f"{playlist_id:<37} | {title:<50} | ")
                    sys.stdout.write(f"{('X' if download_info and download_info.music_videos else ''):^16} | ")
                    sys.stdout.write(f"{str(download_info.download_path) if download_info else '':<50}\n")
                    sys.stdout.flush()

            elif args.command == "download-playlist":
                youtube = YouTubeAPI()

                for playlist_id in args.playlist_ids:
                    if args.music_videos:
                        youtube.download_music_video_playlist(playlist_id)
                    else:
                        youtube.download_playlist(playlist_id)

                _delete_empty_artist_dirs()

            elif args.command == "refresh-playlists":
                youtube = YouTubeAPI()

                known_playlists = youtube.get_downloaded_playlists()

                for idx, (playlist_id, download_info, playlist_info) in enumerate(known_playlists):
                    logging.status(f"Downloading Playlist {idx+1}/{len(known_playlists)}: {playlist_info['title']}")
                    if download_info.music_videos and args.playlist_type in ["music-video", "all"]:
                        youtube.download_music_video_playlist(playlist_id)
                    elif not download_info.music_videos and args.playlist_type in ["general", "all"]:
                        youtube.download_playlist(playlist_id)

                _delete_empty_artist_dirs()

            elif args.command == "search":
                for video in YouTubeAPI().search(args.youtube_search_query):
                    video.download()

            elif args.command == "moe":
                from web_video_downloader.artist import Artist
                from web_video_downloader.utils import SettingsFile

                youtube = YouTubeAPI()

                everything_history = SettingsFile("audiodb-everything-history") if args.search_engine == "audiodb" else SettingsFile("youtube-everything-history")

                skipped_downloads = SettingsFile("skipped-downloads")

                if args.clear_cache:
                    everything_history.settings.clear()
                    everything_history.save()

                for artist_dir in Path.cwd().iterdir():
                    artist_name = artist_dir.name
                    artist = Artist(artist_name)

                    if not args.reprocess and artist.name in everything_history.settings:
                        logging.success(f"Already downloaded everything for", value=artist)
                        continue

                    console.print_status("-"*120 + f"\nDownloading more of '{artist}'\n" + "-" * 120)

                    search_generator = Video.for_artist(artist) if args.search_engine == "audiodb" else youtube.search(f"{artist.name} music videos")

                    for video in search_generator:
                        if video.view_count < GlobalSettings().min_view_count:
                            logging.warning(f"Skipping download of video with {video.view_count} views", value=video)
                            skipped_downloads.settings.setdefault(artist.name, {})[video.youtube_id] = dict(title=video.song_title, view_count=video.view_count)
                            skipped_downloads.save()
                            continue
                        else:
                            console.print_status(f" -- Downloading {video}")
                            video.download()

                    everything_history.settings[artist.name] = True
                    everything_history.save()

                _delete_empty_artist_dirs()

            elif args.command == "update-plex":
                GlobalSettings().permissive = True
                # GlobalSettings().interactive = True

                Plex(args.library_name).update_library(args.update_cache_for_artist)

            elif args.command == "cleanup-plex":
                GlobalSettings().permissive = True
                GlobalSettings().interactive = True

                Plex(args.library_name).cleanup_library()

            elif args.command == "prune":
                _delete_empty_artist_dirs()
                _remove_duplicate_videos()

            elif args.command == "reprocess":
                from web_video_downloader.utils import match_title
                from web_video_downloader.artist import Artist

                GlobalSettings().permissive = True
                GlobalSettings().interactive = True
                GlobalSettings().download_dir = Path.cwd()
                # go through each obj file and perform any cleanup actions

                # delete any old video obj files
                logging.status(f"Deleting all VIDEO OBJ files...")
                if not args.dryrun:
                    subprocess.run("find . -name *.video.obj -exec rm -f {} \\;", shell=True)

                # used to look for duplicates using simple song_title (not full_title, which can often differ)
                video_map = {}
                badly_formatted_files = []

                counter = 0
                for artist_dir in Path.cwd().iterdir():
                    if not artist_dir.is_dir() or artist_dir.name.startswith("."):
                        continue

                    artist_name = artist_dir.name
                    artist = Artist(artist_name)

                    if not args.dryrun:
                        artist.save_obj_file()

                    console.print_status("-"*120 + f"\n{artist}\n" + "-" * 120)
                    for mp4 in artist_dir.rglob("*.mp4"):
                        counter += 1
                        logging.info(f"  - {counter:04} {mp4}")

                        try:
                            name = f"{artist_name} - {mp4.stem.split('-', maxsplit=1)[1].strip()}"
                        except IndexError:
                            badly_formatted_files.append(mp4)
                            continue

                        matched_title = match_title(name)
                        try:
                            video = Video.for_artist_and_song(artist.name, matched_title.song_title,
                                                            full_title=matched_title.full_song_title)
                        except SkipVideo:
                            print("")
                            if input("Do you want to delete this video? (y/n)").lower() == "y":
                                mp4.unlink()
                            continue

                        video_map.setdefault(artist.name, {}).setdefault(video.full_title.lower().strip(), []).append(mp4)

                        logging.info(f"     - {video}")
                        if mp4 != video.download_path:
                            logging.debug(f"     - FROM: {mp4}")
                            logging.debug(f"     - TO: {video.download_path}")
                            if not args.dryrun:
                                shutil.move(mp4, video.download_path)

                        jpg_path = mp4.parent / f"{mp4.stem}.jpg"
                        jpg_to_path = video.download_path.parent / f"{video.download_path.stem}.jpg"
                        vtt_path = mp4.parent / f"{mp4.stem}.en.vtt"
                        vtt_to_path = video.download_path.parent / f"{video.download_path.stem}.en.vtt"

                        if jpg_path.exists() and jpg_path != jpg_to_path:
                            logging.debug(f"     - JPG FROM: {jpg_path}")
                            logging.debug(f"     - JPG TO: {jpg_to_path}")
                            if not args.dryrun:
                                shutil.move(jpg_path, jpg_to_path)

                        if vtt_path.exists() and vtt_path != vtt_to_path:
                            logging.debug(f"     - VTT FROM: {vtt_path}")
                            logging.debug(f"     - VTT TO: {vtt_to_path}")
                            if not args.dryrun:
                                shutil.move(vtt_path, vtt_to_path)

                        if not args.dryrun:
                            video.save_obj_file()

                    # delete all album dirs in the artist dir
                    for album_dir in artist_dir.iterdir():
                        if not album_dir.is_dir():
                            continue

                        if album_dir.is_dir() and album_dir.name.startswith("S"):
                            logging.info(f"     - DELETE ALBUM DIR: {album_dir}")
                            if not args.dryrun:
                                shutil.rmtree(album_dir)

                logging.info("-" * 120)
                logging.info("-" * 120)
                logging.info("-" * 120)

                for artist_name, title_map in video_map.items():
                    for title, file_list in title_map.items():
                        if len(file_list) > 1:
                            logging.warning(f"Deleting duplicates", value=f"{artist_name} -> {title}")
                            if not args.dryrun:
                                for path in file_list[1:]:
                                    path.unlink()

                logging.info("-" * 120)
                logging.info("-" * 120)
                logging.info("-" * 120)

                for bad_file in badly_formatted_files:
                    logging.warning(f"Deleting file with malformed name", value=bad_file)
                    if not args.dryrun:
                        bad_file.unlink()

            elif args.command == "analyze":
                for video in Video.from_found_obj_files("Video"):
                    print(video.view_count)

            else:
                raise ValueError(f"Invalid command: {args.command}")

        except KeyboardInterrupt:
            print("")


if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description="Web Video Downloader Tool")
    DownloaderTool(parser).main()
