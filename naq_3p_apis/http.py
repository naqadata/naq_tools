
from naq_utils.extensions import Path
import urllib3


def download_file(url: str, filename_path: Path):
    """Stream a remote file to disk.

    Args:
        url: Fully qualified URL pointing to the resource to download.
        filename_path: Local filesystem path where the file should be saved.
    """
    http = urllib3.PoolManager()
    req = http.request("GET", url, preload_content=False)

    filename_path.parent.mkdir(exist_ok=True, parents=True)

    if filename_path.exists():
        return

    with filename_path.open("wb") as f:
        while True:
            data = req.read(1024)
            if not data:
                break
            f.write(data)
    req.release_conn()
