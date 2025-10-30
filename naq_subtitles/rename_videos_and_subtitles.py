#!/usr/bin/env python3

from pathlib import Path
import re
import shutil
import argparse
from typing import TypeAlias
from dataclasses import dataclass

from naq_utils.naq_tool import NaqTool
from naq_utils.custom_logging import logger


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

class File:
    def __init__(self, path: Path):
        self.path = path

    def get_episode_tag(self, season_num: int | None = None, episode_num: int | None = None) -> str | None:
        """
        If a regex mathches the file's name, an episode tag will be returned, otherwise None
        """
        for regex in regexes:
            match = re.search(regex, self.path.name, flags=re.IGNORECASE)
            if match:
                season_match, episode_match = int(match.group(1)), int(match.group(2))
                season, episode = (season_num or season_match), (episode_num or episode_match)
                return f"S{season:02}E{episode:02}" 
            
        return None

    def is_supported_video(self) -> bool:
        return self.path.suffix.lower() in ('.mkv', '.mp4', '.m4v', '.avi')
    
    def is_supported_subtitle(self) -> bool:
        return self.path.suffix.lower() in ('.srt', '.ass', '.vtt')


@dataclass
class FilePair:
    video: File = None
    subtitle: File = None

EpisodeTag: TypeAlias = str


class RenameTool(NaqTool):

    def _populate_parser(self):
        self.parser.add_argument("--root-dir", type=Path, required=False, default=Path.cwd(), help="Location to begin search for matching files. Default: Current Directory")
        self.parser.add_argument("--season", type=int, required=False, default=None, help="Apply given season number to all episodes, regardless of current filenames")
        self.parser.add_argument("--start-episode", type=int, required=False, default=None, help="Apply episode number manually, starting with given value, regardless of current filenames")

    def main(self, args: argparse.Namespace):
        file_map: dict[EpisodeTag, FilePair] = {} 

        season_override = args.season
        manual_episode_num = args.start_episode
        root_dir = args.root_dir or Path.cwd()

        show_name = root_dir.absolute().parent.name

        logger.info(f"Scanning Directory", value=root_dir)
        logger.info(f"Show name", value=show_name)

        sorted_entries = [File(p) for p in sorted(list(root_dir.iterdir()))]

        for listed_file in sorted_entries:
            ep_tag: EpisodeTag = listed_file.get_episode_tag(season_num=season_override, episode_num=manual_episode_num)
            if ep_tag:
                manual_episode_num = manual_episode_num + 1 if manual_episode_num else None

                if listed_file.is_supported_video():
                    file_map.setdefault(ep_tag, FilePair()).video = listed_file
                elif listed_file.is_supported_subtitle():
                    file_map.setdefault(ep_tag, FilePair()).subtitle = listed_file
                else:
                    logger.debug(f"Ignoring unsupported file: {listed_file}")

        renames: dict[EpisodeTag, tuple[Path, Path]] = {}

        logger.info("")
        logger.info("Proposed File Names")
        logger.info("=" * 152)
        logger.info(f"= {'Episode':^20} || {'Video':^60} || {'Subtitles':^60} =")
        logger.info("=" * 152)
        for ep_tag in sorted(file_map.keys()):
            listed_file = file_map[ep_tag]

            new_video_filename = f"{show_name} {ep_tag}{listed_file.video.path.suffix.lower()}" if listed_file.video else ""
            new_subtitle_filename = f"{show_name} {ep_tag}.en{listed_file.subtitle.path.suffix.lower()}" if listed_file.subtitle else ""

            logger.info(f"= {ep_tag:20} || {new_video_filename:60} || {new_subtitle_filename:60} =")

            if listed_file.video:
                renames.setdefault(ep_tag, []).append((listed_file.video.path, listed_file.video.path.parent / new_video_filename))

            if listed_file.subtitle:
                renames.setdefault(ep_tag, []).append((listed_file.subtitle.path, listed_file.subtitle.path.parent / new_subtitle_filename))
# 
        logger.info("=" * 152)

        try:
            input("\nTo continue and rename, press enter. To quit, Ctrl-C")
        except KeyboardInterrupt:
            print("\nExiting rename_with_subtitles...")
            return
        else:
            print("")
            for ep_tag, tag_renames in renames.items():
                for src, dest in tag_renames:
                    if src and dest:
                        logger.info(f"{ep_tag} -- {src} ==> {dest}")
                        shutil.move(src, dest)


def main():
    parser = argparse.ArgumentParser(description="Rename video files, along with SRT files")
    tool = RenameTool(parser)
    tool.main(parser.parse_args())


if __name__ == '__main__':
    main()