import argparse
import signal
from web_video_downloader.__main__ import DownloaderTool
from video_utils.rename_with_subtitles import RenameTool


def handle_sigint(signum, frame):
    print("\nExiting naq_tools...")
    exit(0)


def main():
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser(description="NAQADATA Tools")
    subparsers = parser.add_subparsers(dest="tool", required=True)

    downloader_parser = subparsers.add_parser("downloader", help="Web Video Downloader Tool")
    downloader_tool = DownloaderTool(downloader_parser)
    
    rename_parser = subparsers.add_parser("rename", help="Rename video files, along with SRT files")
    rename_tool = RenameTool(rename_parser)

    args = parser.parse_args()

    if args.tool == "downloader":
        downloader_main(parser)
    elif args.tool == "rename":
        rename_main(parser) 

    import time
    time.sleep(5)

    return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting naq_tools...")
        