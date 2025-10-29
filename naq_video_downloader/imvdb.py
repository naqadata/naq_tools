import time
from typing import Generator

import urllib3
import urllib.parse
import json

from naq_utils import custom_logging as logging
from naq_video_downloader.utils import RequestCache

IMVDB_API_KEY = "oPA5IK14HVj9srjiAa6O6eYicQdnWXHBFcnr8kVG"
IMVDB_URL = "https://imvdb.com/api/v1/"

MAX_SEARCH_RESULTS = 100


# noinspection DuplicatedCode
class IMVDB:
    _cache = RequestCache("imvdb-api")
    _http_pool = None

    @classmethod
    def _request(cls, path: str, params: dict[str, str], update_cache: bool = False) -> dict | None:
        headers = {
            "x-rapidapi-host": "imvdb.com",
            "x-rapidapi-key": IMVDB_API_KEY
        }

        if update_cache:
            cls._cache.delete_response([path, params])

        cached_response = cls._cache.get_response([path, params])
        if cached_response:
            return cached_response

        arg_string = urllib.parse.urlencode(params) if params else ""
        url = urllib.parse.urljoin(IMVDB_URL, path) + f"?{arg_string}"

        logging.debug(f"Requesting '{url}'")

        if cls._http_pool is None:
            cls._http_pool = urllib3.PoolManager()

        attempts = 0
        while attempts < 3:

            response = cls._http_pool.request("GET", url, headers=headers)
            if response.status >= 500:
                logging.warning(f"Request '{url}' failed with status code '{response.status}'. Retrying in 2 seconds...")
                time.sleep(2)
                attempts += 1
                continue
            else:
                assert response.status == 200, f"Bad response ({response.status}): {response.data}"
                response_json = json.loads(response.data)
                cls._cache.cache_response([path, params], response_json)
                return response_json

        return None

    @classmethod
    def search(cls, query: str) -> Generator[dict, None, None]:
        current_page = 1
        num_returned = 0

        logging.info(f"Searching IMVDB for '{query}'")

        while True:
            response = cls._request("search/videos", {"q": query, "per_page": 25, "page": current_page})
            if response["current_page"] >= response["total_pages"]:
                break
            current_page = current_page + 1

            for result in response.get("results", []):
                yield result

                num_returned += 1
                if num_returned >= MAX_SEARCH_RESULTS:
                    return

    @classmethod
    def for_youtube_id(cls, query: str | list[str], youtube_id: str) -> dict | None:
        query = " ".join(query) if isinstance(query, list) else query

        for (idx, result) in enumerate(cls.search(query)):
            video_details = cls._request(f"video/{result['id']}", {"include": "sources"})
            if video_details:
                for source in video_details.get("sources", []):
                    if source["source_data"] == youtube_id:
                        return video_details
        else:
            logging.warning(f"Did not find result for '{youtube_id}' for query '{query}' within {MAX_SEARCH_RESULTS} entries")
            return None


def main():
    import argparse

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("artist")
    search_parser.add_argument("--youtube-id", default=None, help="YouTube ID")
    args = parser.parse_args()

    if args.command == "search":
        try:
            if args.youtube_id:
                print(IMVDB.for_youtube_id(args.artist, args.youtube_id))
            else:
                print(IMVDB.search(args.artist))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
