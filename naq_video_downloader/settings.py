from dataclasses import dataclass

from naq_utils.extensions import Path
from naq_utils.settings import GSBool, GSInt, GSPath, GSStr


@dataclass
class GlobalSettings:
    download_dir: GSPath = GSPath("download_dir", Path.home() / ".naq_tools/downloads")
    interactive: GSBool = GSBool("interactive", False)
    permissive: GSBool = GSBool("permissive", False)
    min_view_count: GSInt = GSInt("min_view_count", 0)
    audiodb_api_key: GSStr = GSStr("audiodb_api_key", "")
    google_api_key: GSStr = GSStr("google_api_key", "")
    imvdb_api_key: GSStr = GSStr("imvdb_api_key", "")
