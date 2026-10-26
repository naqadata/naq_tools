import argparse
import signal
import sys
from naq_video_downloader.__main__ import DownloaderTool
from naq_utils.logging import logger
from naq_subtitles.__main__ import SubtitlesTool
import logging


def handle_sigint(signum, frame):
    print("\nExiting naq_tools...")
    exit(0)


def _parse_args(parser: argparse.ArgumentParser, argv: list[str] | None = None) -> argparse.Namespace:
    """Parse toolbox arguments, retaining tokens after ``--`` for yt-dlp."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        separator_index = argv.index("--")
    except ValueError:
        toolbox_args, yt_dlp_args = argv, []
    else:
        toolbox_args, yt_dlp_args = argv[:separator_index], argv[separator_index + 1:]

    args = parser.parse_args(toolbox_args)
    if yt_dlp_args and args.tool != "downloader":
        parser.error("yt-dlp passthrough options (after --) are only valid for the downloader tool")
    args.yt_dlp_args = yt_dlp_args
    return args


def main(argv: list[str] | None = None):
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser(description="NAQADATA Tools")

    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", 
                        help="Set the logging level. (default: %(default)s)")

    subparsers = parser.add_subparsers(dest="tool", required=True)

    downloader_tool = DownloaderTool(subparsers.add_parser("downloader", help="Web Video Downloader Tool"))
    subtitles_tool = SubtitlesTool(subparsers.add_parser("subtitles", help="Subtitle operations (i.e. Generation, Renaming, etc)"))

    args = _parse_args(parser, argv)

    logger.setLevel(getattr(logging, args.log_level.upper()))

    if args.tool == "downloader":
        downloader_tool.main(args)
    elif args.tool == "subtitles":
        subtitles_tool.main(args)


if __name__ == "__main__":
    main()
        
