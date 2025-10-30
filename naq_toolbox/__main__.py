import argparse
import signal
from naq_video_downloader.__main__ import DownloaderTool
from naq_utils.custom_logging import logger
from naq_subtitles.__main__ import SubtitlesTool
import logging


def handle_sigint(signum, frame):
    print("\nExiting naq_tools...")
    exit(0)


def main():
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser(description="NAQADATA Tools")

    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", 
                        help="Set the logging level. (default: %(default)s)")

    subparsers = parser.add_subparsers(dest="tool", required=True)

    downloader_tool = DownloaderTool(subparsers.add_parser("downloader", help="Web Video Downloader Tool"))
    subtitles_tool = SubtitlesTool(subparsers.add_parser("subtitles", help="Subtitle operations (i.e. Generation, Renaming, etc)"))

    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level.upper()))

    if args.tool == "downloader":
        downloader_tool.main(args)
    elif args.tool == "subtitles":
        subtitles_tool.main(args)


if __name__ == "__main__":
    main()
        