#!/usr/bin/env python
import argparse
import subprocess
import sys
import json
import shutil
from typing import Optional
from pathlib import Path
from colorama import Fore, Style
from tempfile import TemporaryDirectory


def print_status(msg: str):
    print(Fore.BLUE + msg + Style.RESET_ALL)


def run_cmd_oneline(cmd: str):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    while proc.poll() is None:
        for line in proc.stdout:
            sys.stdout.write(" " * 100)  # clear the prev line to avoid noise
            sys.stdout.write("\r")
            sys.stdout.write(line.strip()[:80])
            sys.stdout.write("\r")

    sys.stdout.write(" " * 100)  # clear the last line to avoid noise
    sys.stdout.write("\r")

    return proc.returncode


def iter_video_files(path: Path):
    assert path.is_dir()

    sorted_entries = sorted(path.iterdir())

    for entry in sorted_entries:
        if entry.is_dir():
            for _ in iter_video_files(entry):
                yield _
        elif entry.suffix in ('.mkv', '.mp4', '.m4v', '.avi'):
            yield entry


def get_video_height(path: Path) -> Optional[int]:
    result = subprocess.run(f"ffprobe -print_format json -show_streams '{path}'", shell=True, capture_output=True,
                            text=True)

    heights = []
    output = json.loads(result.stdout)
    for stream in output.get("streams", []):
        if stream['codec_type'].lower() == "video":
            return stream["height"]


def encode_file(path: Path, preset: str):
    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        print_status(f"Encoding '{path.name}' with preset '{preset}'")

        output_path = tmp_dir / f"{path.stem}.mp4"
        final_path = path.parent / output_path.name

        cmd = f"HandBrakeCLI --preset '{preset}' --input '{path}' --output '{output_path}' --encoder x265"
        assert run_cmd_oneline(cmd) == 0
        print("")

        shutil.move(output_path, final_path)

        print(f"  -- New video: {final_path}")


def main(start_path: Path):
    for video_file_path in iter_video_files(start_path):
        height = get_video_height(video_file_path)
        preset = "Apple 2160p60 4K HEVC Surround" if height > 1080 else \
            "Apple 1080p30 Surround" if height > 720 else \
            "Fast 720p30" if height > 540 else \
            "Apple 540p30 Surround"

        encode_file(video_file_path, preset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--presets", action="store_true", default=False, help="List all presets")
    parser.add_argument("--start-path", help="path at which to start", default=".", required=False)
    args = parser.parse_args()

    if args.presets:
        subprocess.run(f"HandBrakeCLI --preset-list", shell=True)
        sys.exit(0)

    try:
        main(Path(args.start_path).absolute())
    except KeyboardInterrupt:
        print("")
