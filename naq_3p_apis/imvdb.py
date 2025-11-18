from typing import Generator

from naq_3p_apis.api import Api
from naq_utils.logging import logger


IMVDB_URL = "https://imvdb.com/api/v1/"

DEFAULT_MAX_RESULTS = 100
YOUTUBE_MAX_RESULTS = 2

# noinspection DuplicatedCode
class IMVDB(Api):
    _http_pool = None

    def __init__(self, api_key: str):
        super().__init__("imvdb", api_key, IMVDB_URL)

    def search(self, query: str, max_results: int = DEFAULT_MAX_RESULTS) -> Generator[dict, None, None]:
        current_page = 1
        num_returned = 0

        logger.info(f"Searching IMVDB for '{query}'")

        while True:
            response = self._request("search/videos", {"q": query, "per_page": "50", "page": str(current_page)})
            if not response:
                return
            
            if response["current_page"] >= response["total_pages"]:
                break
            
            current_page = current_page + 1

            for result in response.get("results", []):
                yield result

                num_returned += 1
                if num_returned >= max_results:
                    return
                
    def for_imvdb_id(self, imvdb_id: str) -> dict | None:
        return self._request(f"video/{imvdb_id}", {"include": "sources"})

    def for_youtube_id(self, query: str | list[str], youtube_id: str) -> dict | None:
        query = " ".join(query) if isinstance(query, list) else query

        for result in self.search(query, max_results=YOUTUBE_MAX_RESULTS): # just check the first 2 entries. unlikely to find the youtube entry beyond that
            video_details = self.for_imvdb_id(result["id"])
            if video_details:
                for source in video_details.get("sources", []):
                    if source["source_data"] == youtube_id:
                        return video_details
        else:
            logger.warning(f"Did not find YouTube ID '{youtube_id}' for query '{query}' within first {YOUTUBE_MAX_RESULTS} results returned from IMVDB")
            