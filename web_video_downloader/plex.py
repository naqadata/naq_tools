import plexapi
from plexapi.myplex import MyPlexAccount
from plexapi.video import Show as PlexArtist, Episode as MusicVideo
from plexapi.server import PlexServer
from plexapi.library import ShowSection
from plexapi.media import Media
from plexapi.playlist import Playlist
import plexapi.exceptions
from typing import Optional, List, Tuple

from naqacommon.console import print_status, print_success, print_warning, print_temp
from naqacommon import custom_logging as logging
from web_video_downloader.media_server import MediaServer
from web_video_downloader.theaudiodb import TheAudioDBAPI
from web_video_downloader.utils import GlobalSettings
from web_video_downloader.exceptions import ArtistNotFoundInPlex, VideoNotFoundInPlex, SkipVideo, TrackNotFound
from pathlib import Path
import os
import re


class Plex(MediaServer):
    def __init__(self, library_name: str):
        super().__init__(library_name)

        self._account = MyPlexAccount("pauldwitt", os.environ.get("PLEX_PASSWORD"))
        self._plex: PlexServer = self._account.resource("Tiny Rick").connect(ssl=True)
        self._music_videos: ShowSection = self._plex.library.section(library_name)
        self._music_videos_path: Path = self._music_videos.locations[0]

        GlobalSettings().download_dir = self._music_videos_path

    def get_artist(self, artist_name: str) -> PlexArtist:
        try:
            return self._music_videos.get(artist_name)
        except plexapi.exceptions.NotFound:
            # try with a sanitized artist name bc Plex is weird
            try:
                sanitized_artist_name = re.sub(r"[.\-/]", " ", artist_name).strip()
                sanitized_artist_name = re.sub(r"\s+", " ", sanitized_artist_name)
                return self._music_videos.get(sanitized_artist_name)
            except plexapi.exceptions.NotFound as e:
                raise ArtistNotFoundInPlex(artist_name) from e

    def get_music_video(self, artist_name: str, episode: int) -> MusicVideo:
        try:
            return self.get_artist(artist_name).episode(season=1, episode=episode)
        except plexapi.exceptions.NotFound:
            raise VideoNotFoundInPlex(artist_name, episode)

    def get_playlist(self, playlist_name: str) -> Optional[Playlist]:
        try:
            return self._plex.playlist(playlist_name)
        except plexapi.exceptions.NotFound:
            return None

    def get_playlists(self) -> List[Playlist]:
        return self._plex.playlists(title="*Music Videos*")

    def create_playlist(self, playlist_name: str, videos: List[MusicVideo]) -> Playlist:
        return self._plex.createPlaylist(playlist_name, items=videos)

    def cleanup_library(self):
        from collections import Counter

        res_counter = Counter()
        filtered_counter = Counter()

        for plex_artist in self._music_videos.search():  # type: PlexArtist
            for plex_video in plex_artist.episodes():  # type: MusicVideo
                for media in plex_video.media:
                    if media.height < 480:
                        print(f"Deleting below-res video: {media}")
                        media.delete()
                res_counter[plex_video  .media[0].height] += 1

        for height, count in res_counter.most_common():
            if height >= 480:
                filtered_counter["above480"] += count
            else:
                filtered_counter["below480"] += count

        for thresh, count in filtered_counter.most_common():
            print(f"{thresh}: {count}")


    def update_library(self, update_cache_for_artist: str = None):
        from web_video_downloader.utils import match_title
        from web_video_downloader.artist import Artist
        from web_video_downloader.video import Video

        for playlist in self._music_videos.playlists():  # type: Playlist
            playlist.delete()

        console_idx = 1

        new_playlists = {
            "by_decade": {},
            "by_genre": {},
            "by_decade_and_genre": {}
        }

        for plex_artist in self._music_videos.search():  # type: PlexArtist
            artist_name = plex_artist.title
            artist = Artist(artist_name)

            plex_artist.edit(**artist.metadata)

            print_status("-" * 120 + f"\n{plex_artist}\n{artist}\n" + "-" * 120)

            plex_artist_updates: List[Tuple[MusicVideo, Video]] = []

            update_cache = update_cache_for_artist.lower() == artist_name.lower() if update_cache_for_artist else False

            for plex_video in plex_artist.episodes():  # type: MusicVideo
                media: Media = plex_video.media[0]
                mp4 = Path(media.parts[0].file)

                mp4_artist_name = mp4.parent.name
                mp4_song_title = mp4.stem.split('-', maxsplit=1)[1].strip()

                matched_title = match_title(f"{mp4_artist_name} - {mp4_song_title}")
                logging.info(f"{matched_title}")

                video = None
                try:
                    video = Video.for_artist_and_song(matched_title.artist_name, matched_title.song_title, full_title=matched_title.full_song_title, update_cache=update_cache)

                    try:
                        album_info = TheAudioDBAPI().album_info(video.info["idAlbum"], update_cache=update_cache) if "idAlbum" in video.info else None
                        if album_info:
                            video.year_released = int(album_info.get("intYearReleased"))

                            decade_name = None
                            # add to by-decade playlists
                            if video.year_released:
                                decade_name = f"{int(video.year_released / 10) * 10}s"
                                new_playlists["by_decade"].setdefault(decade_name, []).append(plex_video)

                            genre = album_info.get("strGenre")
                            if genre:
                                new_playlists["by_genre"].setdefault(genre, []).append(plex_video)

                            if decade_name and genre:
                                new_playlists["by_decade_and_genre"].setdefault(f"{genre} ({decade_name})")
                    except Exception as e:
                        raise
                except SkipVideo:
                    print(f"Skipping video for '{mp4_song_title}' by '{mp4_artist_name}'")
                    continue
                except TrackNotFound:
                    print(f"Track info not found for: {mp4_song_title}")

                if video:
                    print(f"[{console_idx:04}] - {video}")
                    console_idx += 1
                    plex_artist_updates.append((plex_video, video))

            # sort the plex updates for this artist, by album year released
            plex_artist_updates.sort(key = lambda update: update[1].year_released, reverse=True)
            for idx, (plex_video, video) in enumerate(plex_artist_updates):
                video.episode_num = idx + 1
                plex_video.edit(**video.metadata)

        for decade_name, playlist_items in new_playlists["by_decade"].items():
            self.create_playlist(decade_name, playlist_items)
            print_success(f"Created new playlist", value=decade_name)

        ordered_genres = sorted(list(new_playlists['by_genre'].items()), key=lambda x: len(x[1]), reverse=True)

        for decade_name, playlist_items in ordered_genres[:20]:
            self.create_playlist(decade_name, playlist_items)
            print_success(f"Created new playlsit", value=decade_name)

            
