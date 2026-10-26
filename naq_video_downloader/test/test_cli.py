import argparse

from naq_3p_apis.yt_dlp import YT_DLP
from naq_video_downloader.__main__ import DownloaderTool, _parse_args


def test_parser_separates_yt_dlp_passthrough_args():
    parser = argparse.ArgumentParser()
    DownloaderTool(parser)

    args = _parse_args(
        parser,
        [
            "video",
            "video-id",
            "--",
            "--cookies-from-browser",
            "firefox",
        ],
    )

    assert args.targets == ["video-id"]
    assert args.yt_dlp_args == ["--cookies-from-browser", "firefox"]


def test_parser_selects_audio_album_mode():
    parser = argparse.ArgumentParser()
    DownloaderTool(parser)

    args = _parse_args(parser, ["audio-album", "album-url"])

    assert args.targets == ["album-url"]
    assert args.command == "audio-album"


def test_parser_selects_video_album_mode():
    parser = argparse.ArgumentParser()
    DownloaderTool(parser)

    args = _parse_args(parser, ["album", "album-url"])

    assert args.targets == ["album-url"]
    assert args.command == "album"


def test_audio_album_mode_does_not_require_api_keys(monkeypatch, tmp_path):
    parser = argparse.ArgumentParser()
    tool = DownloaderTool(parser)
    downloaded = []
    monkeypatch.setattr(YT_DLP, "download_audio_chapters", lambda target, directory: downloaded.append((target, directory)))

    args = _parse_args(parser, ["audio-album", "--download-dir", str(tmp_path), "album-url"])
    tool.main(args)

    assert downloaded == [("album-url", tmp_path)]
