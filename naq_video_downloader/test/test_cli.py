import argparse

from naq_video_downloader.__main__ import DownloaderTool, _parse_args


def test_parser_separates_yt_dlp_passthrough_args():
    parser = argparse.ArgumentParser()
    DownloaderTool(parser)

    args = _parse_args(
        parser,
        [
            "download",
            "targets",
            "video-id",
            "--",
            "--cookies-from-browser",
            "firefox",
        ],
    )

    assert args.targets == ["video-id"]
    assert args.yt_dlp_args == ["--cookies-from-browser", "firefox"]
