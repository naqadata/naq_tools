#!/usr/bin/env python3

import argparse
import logging
from pathlib import Path
from naq_utils.naq_tool import NaqTool
import subprocess


class ReprocessSubsTool(NaqTool):
    def _populate_parser(self):
        pass
        
    def main(self, args: argparse.Namespace):
        for input_file_path in sorted(Path.cwd().rglob("*.srt")):
            logging.info(f"Reprocessing {input_file_path}")
            basename = input_file_path.stem.split(".")[0]
            mp4_file_path = input_file_path.with_name(f"{basename}.mp4")
            if not mp4_file_path.exists():
                logging.warning(f"Corresponding video file {mp4_file_path} not found. Skipping.")
                continue

            try:
                subprocess.run(["naq_tools", "gen_subs", str(mp4_file_path)], cwd=input_file_path.parent, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to reprocess subtitles for {input_file_path}: {e}")
                continue
            else:
                input_file_path.unlink()