#!/usr/bin/env python3

"""Utilities for renaming TV show video files together with their subtitles.

This module scans a directory of video and subtitle files for common TV
episode patterns (for example "S01E02" or "1x02") and proposes new
filenames normalized to the format: "<Show Name> S<season>E<episode>[.en].ext".

It exposes a small set of classes:
- File: represents a single file on disk and extracts episode tags
- EpisodeFiles: container for video+subtitle pairs for a single episode
- FileMap: collection of EpisodeFiles with rename proposals and execution
- RenameTool: CLI wrapper that wires everything together

The module is intended to be used as a command-line tool but the classes
are small and testable individually.
"""

from pathlib import Path
import re
import shutil
import argparse
from typing import TypeAlias, Iterator
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

EpisodeTag: TypeAlias = str

class File:
    """Representation of a file (video or subtitle) with episode metadata.

    Attributes:
        path: Path to the file on disk.
        _show_name: Name of the show (used when constructing new filenames).
        _season_override: Optional season number supplied by the user; if set
            this value is used instead of any season parsed from the filename.
        _episode_override: Optional starting episode number supplied by the
            user; if set this value is used instead of any episode parsed from
            the filename.
        _episode_tag: Cached normalized episode tag (e.g. "S01E02") or None.
    """

    def __init__(self, path: Path, show_name: str, season_num: int | None = None, episode_num: int | None = None):
        self.path = path
        self._show_name = show_name
        self._season_override = season_num
        self._episode_override = episode_num

        self._episode_tag: EpisodeTag | None = None

    def __repr__(self) -> str:
        return f"File[{self.path.name}]"

    @classmethod
    def from_root_dir(cls, root_dir: Path, season_num: int | None = None, starting_ep_num: int | None = None):
        """Return a sorted list of `File` objects for files in `root_dir`.

        The show name is inferred from the parent directory of `root_dir` and
        each entry in `root_dir` is wrapped in a `File`. If `starting_ep_num`
        is provided, it will be used for the first file and incremented for
        each subsequent file.

        Args:
            root_dir: Directory containing episode files.
            season_num: Optional season override to apply to every yielded File.
            starting_ep_num: Optional starting episode number to assign
                sequentially to files.

        Returns:
            A sorted list of `File` instances for each file in `root_dir`.
        """

        show_name = root_dir.absolute().parent.name

        logger.info(f"Scanning Directory", value=root_dir)
        logger.info(f"Show name", value=show_name)

        files: list[File] = []

        episode_num = starting_ep_num
        for path in sorted(list(root_dir.iterdir())):
            files.append(File(path, show_name, season_num=season_num, episode_num=episode_num))
            episode_num = episode_num + 1 if episode_num else None

        return sorted(files, key=lambda x: x.episode_tag or "")
            
    @property
    def episode_tag(self) -> str | None:
        """Return a normalized episode tag parsed from the filename.

        The result is cached on the instance. If a matching pattern is found
        in the filename a string of the form "S{season:02}E{episode:02}" is
        returned. If the filename doesn't contain a recognizable episode
        pattern, None is returned.
        """
        if not self._episode_tag:
            for regex in regexes:
                match = re.search(regex, self.path.name, flags=re.IGNORECASE)
                if match:
                    season_match, episode_match = int(match.group(1)), int(match.group(2))
                    season, episode = (self._season_override or season_match), (self._episode_override or episode_match)
                    self._episode_tag = f"S{season:02}E{episode:02}" 
                    break
            
        return self._episode_tag
    
    def parse_episode_tag(self) -> tuple[int|None, int|None]:
        """Parse the cached normalized episode tag into (season, episode).

        Returns a tuple of two ints (season, episode). If the file has no
        episode tag, returns (None, None).
        """

        if not self.episode_tag:
            return None, None

        match = re.search(r"S(\d+)E(\d+)", self.episode_tag)
        assert match, f"Episode tag is somehow formatted badly: {self.episode_tag}"
        return int(match.group(1)), int(match.group(2))

    def is_supported_video(self) -> bool:
        """Return True if the file extension is a supported video format."""

        return self.path.suffix.lower() in ('.mkv', '.mp4', '.m4v', '.avi')
    
    def is_supported_subtitles(self) -> bool:
        """Return True if the file extension is a supported subtitle format."""

        return self.path.suffix.lower() in ('.srt', '.ass', '.vtt')
    
    @property
    def new_filename(self) -> str | None:
        """Construct the new filename proposed for this File.

        For videos the filename will be: "<Show Name> <EpisodeTag><ext>".
        For subtitles the filename will include an ".en" language marker before
        the extension: "<Show Name> <EpisodeTag>.en<ext>". If the file type is
        not recognized, None is returned.
        """

        return \
            f"{self._show_name} {self.episode_tag}{self.path.suffix.lower()}" if self.is_supported_video() else \
            f"{self._show_name} {self.episode_tag}.en{self.path.suffix.lower()}" if self.is_supported_subtitles() else None
    

@dataclass
class EpisodeFiles:
    video: File | None = None
    subtitles: File | None = None

    def set(self, file: File):
        """Assign a `File` to this episode's video or subtitles slot.

        The method inspects the file extension and stores it in the appropriate
        attribute. Unsupported file types are ignored and logged at debug
        level.
        """

        if file.is_supported_video():
            self.video = file
        elif file.is_supported_subtitles():
            self.subtitles = file
        else:
            logger.debug(f"Ignoring unsupported file: {file}")


class FileMap:
    """Collection of episode tag -> EpisodeFiles and proposed renames.

    The FileMap gathers `File` instances by episode tag, builds a list of the
    rename operations that would normalize filenames, and can print a summary
    or execute the renames on disk.
    """

    def __init__(self):
        self._map: dict[EpisodeTag, EpisodeFiles] = {}
        self._renames: dict[EpisodeTag, list[tuple[Path, Path]]] = {}

    def add(self, file: File):
        """Add a file to the map under `ep_tag` and record its proposed rename.

        Args:
            file: File instance to add.
        """
        ep_tag = file.episode_tag
        if not ep_tag:
            logger.info(f"Ingoring file that has no episode tag: {file}")
            return

        self._map.setdefault(ep_tag, EpisodeFiles()).set(file)
        if file.new_filename:
            self._renames.setdefault(ep_tag, []).append((file.path, file.path.parent / file.new_filename))

    def log_summary(self):
        """Log a formatted summary of proposed new filenames.

        The output lists each episode tag and the corresponding proposed video
        and subtitle filenames.
        """

        logger.info("")
        logger.info("Proposed File Names")
        logger.info("=" * 140)
        logger.info(f"= {'Episode':^8} || {'Video':^60} || {'Subtitles':^60} =")
        logger.info("=" * 140)

        for ep_tag in sorted(self._map.keys()):
            episode_files = self._map[ep_tag]
            video_filename = episode_files.video.new_filename if episode_files.video else ""
            subtitles_filename = episode_files.subtitles.new_filename if episode_files.subtitles else ""
            logger.info(f"= {ep_tag:^8} || {video_filename:60} || {subtitles_filename:60} =")

    def execute_renames(self):
        """Perform the recorded rename operations on disk.

        Each recorded (src, dest) pair will be moved using shutil.move and the
        operation is logged. There is no rollback; use with care.
        """

        for ep_tag, tag_renames in self._renames.items():
            for src, dest in tag_renames:
                if src and dest:
                    logger.info(f"{ep_tag} -- {src.name} ==> {dest.name}")
                    shutil.move(src, dest)
            

class RenameTool(NaqTool):

    def _populate_parser(self):
        """Add command-line arguments to the parser used by the tool.

        Arguments added:
            --root-dir: directory to scan for files (defaults to cwd)
            --season: optional integer to force a single season number
            --start-episode: optional starting episode number for sequential
                assignment when filenames lack episode numbers
        """

        self.parser.add_argument("--root-dir", type=Path, required=False, default=Path.cwd(), help="Location to begin search for matching files. Default: Current Directory")
        self.parser.add_argument("--season", type=int, required=False, default=None, help="Apply given season number to all episodes, regardless of current filenames")
        self.parser.add_argument("--start-episode", type=int, required=False, default=None, help="Apply episode number manually, starting with given value, regardless of current filenames")

    def main(self, args: argparse.Namespace):
        """Main entry point for the CLI tool.

        Scans the provided root directory for files, groups them by episode
        tag, prints a summary of the proposed renames, and prompts the user
        to confirm before performing the file moves.
        """

        season_override = args.season
        starting_ep_num = args.start_episode
        root_dir = args.root_dir

        file_map = FileMap()

        for file in File.from_root_dir(root_dir, season_num=season_override, starting_ep_num=starting_ep_num):
            if file.episode_tag:
                file_map.add(file)

        file_map.log_summary()

        try:
            input("\nTo continue and rename, press enter. To quit, Ctrl-C")
        except KeyboardInterrupt:
            print("\nExiting rename_with_subtitles...")
            return
        else:
            print("")
            file_map.execute_renames()


def main():
    parser = argparse.ArgumentParser(description="Rename video files, along with SRT files")
    tool = RenameTool(parser)
    tool.main(parser.parse_args())


if __name__ == '__main__':
    main()