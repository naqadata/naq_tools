import errno
import tempfile
import subprocess
import shutil
import sys
import os

from naq_utils.extensions import Path
from naq_utils.logging import logger


class YT_DLP:
    # Set by the downloader CLI for tokens supplied after its ``--`` separator.
    extra_args: tuple[str, ...] = ()

    @classmethod
    def _command(cls) -> list[str]:
        """Run the yt-dlp installed in the same virtual environment.

        A package installation must not modify its own files at runtime.  Using
        ``python -m yt_dlp`` also avoids accidentally selecting a system-wide
        executable over the dependency installed for naq-toolbox.
        """
        return [sys.executable, "-m", "yt_dlp"]

    @staticmethod
    def _move_downloaded_file(source: Path, destination: Path) -> None:
        """Move a download without copying unsupported metadata across filesystems."""
        try:
            os.replace(source, destination)
        except OSError as error:
            if error.errno != errno.EXDEV:
                raise
            # ``copy2`` (used by shutil.move) copies timestamps and permissions.
            # Windows-mounted WSL drives can reject that metadata operation.
            shutil.copyfile(source, destination)
            source.unlink()
     
    @classmethod
    def download(cls, video_page_url: str, download_path: Path | None = None, file_title: str | None = None, gen_subs: bool = False) -> list[Path]:
        """
        Downloads a video (primarily YouTube) and optionally generates subtitles for it. The method
        uses a specific downloader tool (referenced by a class attribute) to handle the
        video downloading process. The downloaded video can be saved to a specific file
        path or defaults to the current directory. Video thumbnails are also retrieved
        and converted to JPG format. Subtitles can be generated post-download if
        enabled.

        :param youtube_url: A string containing the URL of the YouTube video to
            download.
        :param download_path: An optional pathlib.Path object specifying the directory
            and filename where the downloaded file should be saved. If not provided,
            defaults to using the current directory.
        :param file_title: An optional string used to specify the title of the
            downloaded file.
        :param gen_subs: An optional boolean indicating whether subtitles should be
            generated for the downloaded video.
        :return: A list of pathlib.Path objects representing the downloaded file(s).
        """
        if "t=" in video_page_url:
            logger.warning(f"WTF, a timestamp is in this URL: {video_page_url}")

        logger.status(f"Downloading video from '{video_page_url}'")

        cmd = [
            *cls._command(),
            "-f", "bestvideo+bestaudio/best",
            "--recode", "mp4",
            "--merge-output-format", "mp4",
            "--output", download_path.name if download_path else "%(title)s",
            "--write-thumbnail",  # save the thumbnail for the video
            "--convert-thumbnails", "jpg",  # and convert it to JPG (default is .webp)x
            "--write-subs",  # also save subtitles for the video
            "--quiet",
            "--progress", "--no-warnings",
            "--concurrent-fragments", "5",
            *cls.extra_args,
            video_page_url
        ]

        logger.info(f"YT-DLP CMD: {cmd}")

        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)

            logger.info(f"Downloading video to temp dir", value=tmp_dir)
            completed_proc = subprocess.run(cmd, cwd=tmp_dir)

            download_dir = download_path.parent if download_path else Path.cwd()
            download_dir.mkdir(parents=True, exist_ok=True)

            # if we are generating subtitles, and if we gave gen-subs in our environment...
            if gen_subs:
                if shutil.which("gen-subs"):
                    logger.status(f"Generating subtitles for downloaded video")
                    subprocess.run(["gen-subs", "."], cwd=tmp_dir)
                else:
                    logger.warning("You requested subtitle generation but we are unable to find the 'gen-subs' executable. Reinstall Naq Tools")

            downloaded_file_paths: list[Path] = []

            if completed_proc.returncode == 0:
                for downloaded_file in tmp_dir.iterdir():
                    new_path = download_dir / downloaded_file.name
                    if new_path.exists():
                        new_path.unlink()
                    cls._move_downloaded_file(downloaded_file, new_path)
                    downloaded_file_paths.append(new_path)

            return downloaded_file_paths
