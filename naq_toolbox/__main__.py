import argparse
import signal
from naq_video_downloader.__main__ import DownloaderTool
from naq_utils import custom_logging as logging
import warnings

subtitle_support: bool = True

try:
    from naq_subtitles.__main__ import SubtitlesTool
except (OSError, ValueError, ImportError) as e:
    truncated_error = str(e)[:256] + "..."
    warnings.warn(f"Unable to support subtitle functionality: {truncated_error}")
    subtitle_support = False


def handle_sigint(signum, frame):
    logging.info("Exiting naq_tools...")
    exit(0)


def main():
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser(description="NAQADATA Tools")

    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", 
                        help="Set the logging level. (default: %(default)s)")

    subparsers = parser.add_subparsers(dest="tool", required=True)

    downloader_tool = DownloaderTool(subparsers.add_parser("downloader", help="Web Video Downloader Tool"))

    if subtitle_support:
        subtitles_tool = SubtitlesTool(subparsers.add_parser("subtitles", help="Subtitle operations (i.e. Generation, Renaming, etc)"))

    args = parser.parse_args()

    logging.init(getattr(logging, args.log_level.upper()))

    if args.tool == "downloader":
        downloader_tool.main(args)
    elif subtitle_support and args.tool == "subtitles":
        subtitles_tool.main(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting naq_tools...")
        