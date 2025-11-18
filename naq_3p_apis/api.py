import json
import time
import urllib.parse

import urllib3
from naq_utils.caching import RequestCache
from naq_utils.logging import logger


class Api:
    def __init__(self, name: str, api_key: str, base_url: str):
        self._name = name
        self._api_key = api_key
        self._base_url = base_url
        self._cache = RequestCache(name)

    def _request(self, path: str, params: dict[str, str], update_cache: bool = False, attempts: int = 1) -> dict | None:
        headers = {
            "x-rapidapi-host": urllib.parse.urlparse(self._base_url).netloc,
            "x-rapidapi-key": self._api_key
        }

        if update_cache:
            self._cache.delete([path, params])

        cached_response = self._cache.get([path, params])
        if cached_response:
            return cached_response

        arg_string = urllib.parse.urlencode(params) if params else ""
        url = urllib.parse.urljoin(self._base_url, path) + f"?{arg_string}"

        logger.debug(f"Requesting", value=url)

        if self._http_pool is None:
            self._http_pool = urllib3.PoolManager()

        attempts_made = 0
        while attempts_made < attempts:
            attempts_made += 1
            
            response = self._http_pool.request("GET", url, headers=headers)
            if response.status >= 500:
                logger.warning(f"Request '{url}' failed with status code '{response.status}'. Retrying in 2 seconds...")
                time.sleep(2)
                attempts_made += 1
                continue
            else:
                assert response.status < 300, f"Bad response ({response.status}): {response.data}"
                try:
                    response_json = json.loads(response.data)
                    self._cache.cache([path, params], response_json)
                    return response_json
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response", value=response.data)

        return None