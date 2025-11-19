from typing import Generator

import pyyoutube

from naq_utils.caching import RequestCache
from naq_utils.logging import logger


DEFAULT_MAX_SEARCH_RESULTS = 50

class YouTubeAPI:
    def __init__(self, api_key: str):
        self.api = pyyoutube.Api(api_key=api_key)
        self._playlist_info_cache = RequestCache("yt-playlist-cache")
        self._video_info_cache = RequestCache("yt-video-cache")

    def get_playlist(self, playlist_id: str, *, skip_cache: bool = False) -> pyyoutube.Playlist | None:
        playlist: pyyoutube.Playlist | None = self._playlist_info_cache.get(playlist_id) if not skip_cache else None

        if playlist is None:
            response = self.api.get_playlist_by_id(playlist_id=playlist_id)
            
            if not response:
                return None
            
            assert isinstance(response, pyyoutube.PlaylistListResponse)
            if not response.items:
                return None

            playlist = response.items.pop()
        
            self._playlist_info_cache.cache(playlist_id, playlist)
            logger.success(f"Retrieved playlist info", value=playlist)
        else:
            logger.success(f"Using cached response for playlist", value=playlist)

        return playlist

    def get_video(self, video_id: str, *, skip_cache: bool = False) -> pyyoutube.Video | None:
        video: pyyoutube.Video | None = self._video_info_cache.get(video_id) if not skip_cache else None

        if video is None:
            response = self.api.get_video_by_id(video_id=video_id)

            if not response:
                return None
            
            assert isinstance(response, pyyoutube.VideoListResponse)
            if not response.items:
                return None
            
            video = response.items.pop()

            self._video_info_cache.cache(video_id, video)
            logger.success(f"Fetched video info", value=video)
        else:
            logger.success(f"Using cached response", value=video)

        return video
    
    def get_auto(self, youtube_id: str, skip_cache: bool = False) -> pyyoutube.Video | pyyoutube.Playlist | None:
        return self.get_video(youtube_id, skip_cache=skip_cache) or self.get_playlist(youtube_id, skip_cache=skip_cache)
    
    def iter_playlist_videos(self, playlist_id: str) -> Generator[pyyoutube.Video, None, None]:
        playlist_items = self.api.get_playlist_items(playlist_id=playlist_id, count=None)
        if not playlist_items or not playlist_items.items:
            return
        
        assert isinstance(playlist_items, pyyoutube.PlaylistItemListResponse)
        
        for item in playlist_items.items:
            assert isinstance(item, pyyoutube.PlaylistItem)
            if item.snippet and item.snippet.resourceId and item.snippet.resourceId.videoId:
                video = self.get_video(item.snippet.resourceId.videoId)
                if video:
                    yield video

    def search(self, query: str) -> Generator[pyyoutube.Video, None, None]:
        search_list = self.api.search(q=query, search_type=["video"])
        if not search_list or not search_list.items:
            return
        
        assert isinstance(search_list, pyyoutube.SearchListResponse)

        for search_result in search_list.items:
            assert isinstance(search_result, pyyoutube.SearchResult)
            if search_result.id and search_result.id.videoId:
                video = self.get_video(search_result.id.videoId)
                if video:
                    yield video

    # def get_downloaded_playlists(self) -> List[Tuple[str, YoutubeAPISettings.PlaylistDownloadInfo, Dict]]:
    #     playlist_ids = self._settings_file.known_playlist_ids
    #     playlists = []

    #     for playlist_id in playlist_ids:
    #         playlist_info = self.get_playlist(playlist_id)
    #         download_info = self._settings_file.get_playlist_download_info(playlist_id)
    #         if playlist_info and download_info:
    #             playlists.append((playlist_id, download_info, playlist_info))

    #     playlists.sort(key=lambda x: (not x[1].music_videos, x[2]["title"].lower()))

    #     return playlists

    # def get_playlist_download_info(self, playlist_id: str) -> Optional[YoutubeAPISettings.PlaylistDownloadInfo]:
    #     return self._settings_file.get_playlist_download_info(playlist_id)

    # def get_playlist_items(self, playlist_id: str, playlist_info: Dict = None) -> Generator[Dict, None, None]:
    #     playlist_info = playlist_info or self.get_playlist(playlist_id)

    #     item_responses = []

    #     yt_playlist_items = self.youtube.playlistItems()

    #     request = yt_playlist_items.list(
    #         part="id,snippet,contentDetails",
    #         playlistId=playlist_id,
    #         maxResults=50
    #     )

    #     while request is not None:
    #         try:
    #             response = request.execute()
    #         except TimeoutError:
    #             continue
    #         else:
    #             item_responses.append(response)
    #             request = yt_playlist_items.list_next(request, response)

    #     logger.status(f"Yielding videos from playlist", value=playlist_info["title"])

    #     for response in item_responses:
    #         for item in response['items']:
    #             yield item

    # def get_playlist_videos(self, playlist_id: str) -> Generator[Video, None, None]:
    #     for item in self.get_playlist_items(playlist_id):
    #         try:
    #             video = Video.from_youtube_playlist_item(item)
    #             if video:
    #                 yield video
    #         except (ArtistNotFound, TrackNotFound, SkipVideo) as e:
    #             logger.info(str(e))

    # def search(self, query: str) -> Generator[Video, None, None]:
    #     response = self._request_cache.get_response(f"SEARCH-{query}")
    #     if response is None:
    #         yt_search = self.youtube.search()
    #         request = yt_search.list(
    #             part="id,snippet",
    #             maxResults=50,
    #             q=query,
    #             type="video"
    #         )

    #         response = request.execute()
    #         self._request_cache.cache_response(f"SEARCH-{query}", response)

    #     for item in response["items"]:
    #         try:
    #             video = Video.from_youtube_playlist_item(item)
    #             if video and video.view_count >= GlobalSettings().min_view_count:
    #                 yield video
    #             else:
    #                 logger.warning(f"Skipping video with {video.view_count} views", value=video)
    #         except (ArtistNotFound, TrackNotFound, SkipVideo) as e:
    #             logger.info(str(e))
