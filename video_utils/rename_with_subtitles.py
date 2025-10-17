#!/usr/bin/env python3

from pathlib import Path
import re
import logging
import shutil
import argparse


logging.basicConfig(level=logging.INFO)

regexes = [
        r"S(\d\d).+E(\d\d)",
        r"S(\d\d)E(\d\d)",
        r"SE(\d+)xEP(\d+)",
        r"(\d+)x(\d+)",
        r"Series (\d+) Episode (\d+)",
        r"Season (\d+) Episode (\d+)",
        r"S(\d\d)E(\d\d)",
        r"(\d\d)(\d\d)",
        r"(\d)(\d\d)",
        # DVD rip formats
        r"\w(\d)_t(\d\d)"
]


def populate_parser(parser: argparse.ArgumentParser):
    parser.add_argument("--season", type=int, required=False, default=None)
    parser.add_argument("--start-episode", type=int, required=False, default=None)


def main(parser: argparse.ArgumentParser):
    populate_parser(parser)
    args = parser.parse_args()

    file_map = {}

    show_name = Path().absolute().parent.name

    manual_episode_num = args.start_episode

    sorted_paths = sorted(list(Path().iterdir()))

    for entry in sorted_paths:
        for regex in regexes:
            logging.debug(f"Match {regex} to {entry.name}")
            match = re.search(regex, entry.name, flags=re.IGNORECASE)
            if match:
                season, episode = int(match.group(1)), int(match.group(2))
                season = args.season or season
                if manual_episode_num is not None:
                    episode = manual_episode_num
                    manual_episode_num += 1

                ep_tag = f"S{season:02}E{episode:02}"

                if entry.suffix.lower() in ('.mkv', '.mp4', '.m4v', '.avi'):
                    file_map.setdefault(ep_tag, {})['video'] = entry
                elif entry.suffix.lower() in ('.srt', '.ass' ):
                    file_map.setdefault(ep_tag, {})['subtitle'] = entry
                else:
                    logging.error(f"WTF is this: {entry}")
                break

    logging.debug(f" SHOW NAME: {show_name}\n")

    renames = {}

    for tag in sorted(file_map.keys()):
        entry = file_map[tag]

        video_path = entry.get('video')
        subtitle_path = entry.get('subtitle')

        new_video_path = f"{show_name} {tag}{video_path.suffix.lower()}" if video_path else None
        new_subtitle_path = f"{show_name} {tag}.en{subtitle_path.suffix.lower()}" if subtitle_path else None

        print(tag)
        print(f"  Video:    {video_path} ==> {new_video_path}")
        print(f"  Subtitle: {subtitle_path} ==> {new_subtitle_path}")
        renames.setdefault(tag, {})[video_path] = new_video_path
        renames.setdefault(tag, {})[subtitle_path] = new_subtitle_path

    try:
        input("\nTo continue and rename, press enter. To quit, Ctrl-C")
    except KeyboardInterrupt:
        print("\nExiting rename_with_subtitles...")
        return
    else:
        for tag, tag_renames in renames.items():
            logging.info(f"{tag}")

            for src, dest in tag_renames.items():
                if src and dest:
                    logging.info(f" - {src} ==> {dest}")
                    shutil.move(src, dest)


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        main(parser)
    except KeyboardInterrupt:
        print("\n") 

