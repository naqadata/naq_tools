#!/usr/bin/env python
import contextlib
import os
import shutil
import sys
import time
from typing import Optional

import numpy as np
import torch.cuda
import whisper
import stable_whisper
import argparse
from types import ModuleType
import subprocess
import webvtt
from datetime import timedelta
from colorama import Fore, Style
from moviepy import VideoFileClip
from enum import Enum

from networkx.algorithms.connectivity.edge_augmentation import complement_edges

from naq_utils.extensions import Path
from naq_utils.naq_tool import NaqTool
from naq_utils.logging import logger

class AudioExtractionMethod(Enum):
    MoviePy = "moviepy"
    FFMPEG = "ffmpeg"

def run_cmd_oneline(cmd: str):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    while proc.poll() is None and proc.stdout:
        for line in proc.stdout:
            sys.stdout.write(" " * 100)  # clear the prev line to avoid noise
            sys.stdout.write("\r")
            sys.stdout.write(line.strip()[:80])
            sys.stdout.write("\r")

    sys.stdout.write(" " * 100)  # clear the last line to avoid noise
    sys.stdout.write("\r")

    return proc.returncode


def extracted_audio_moviepy(video_path: Path) -> Path:
    cache_path = Path("~/.subtitle-cache/mp3s").expanduser()
    cache_path.mkdir(exist_ok=True, parents=True)

    audio_path = cache_path / f"{video_path.stem}.mp3"

    if not audio_path.exists():
        logger.warning(f" - Extracting audio from", value=video_path)
        with contextlib.redirect_stdout(open(os.devnull, "w")), contextlib.redirect_stderr(open(os.devnull, "w")):
            video = VideoFileClip(video_path)
            audio = video.audio
            assert audio

            audio.write_audiofile(audio_path, logger=None)

            video.close()
            audio.close()
    else:
        logger.warning(f" - Using cached audio", value=audio_path)

    return audio_path


def extracted_audio_ffmpeg(video_path: Path) -> Path | None:
    cache_path = Path("~/.subtitle-cache/mp3s").expanduser()
    cache_path.mkdir(exist_ok=True, parents=True)

    exts_to_try = ["ac3", "mp3", "aac"]

    for ext in exts_to_try:
        audio_path = cache_path / f"{video_path.stem}.{ext}"

        if not audio_path.exists():
            logger.warning(f" - Extracting audio from", value=video_path)
            if run_cmd_oneline(f'ffmpeg -i "{video_path}" -q:a 0 -map a "{audio_path}"') != 0:
                if audio_path.exists():
                    audio_path.unlink()
                continue
        else:
            logger.warning(f" - Using cached audio", value=audio_path)

        return audio_path

    return None


def has_subtitles(video_path: Path) -> bool:
    ffprobe_path = shutil.which("ffprobe")

    cmd = [
        ffprobe_path,
        "-loglevel", "error",
        "-select_streams", "s",
        "-show_entries",
        "stream=codec_name,index:stream_tags=language",
        "-of", "csv=p=0",
        video_path,
    ]

    completed_proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return completed_proc.returncode == 0 and completed_proc.stdout.strip() != ""

class SubtitleGenerator:
    def __init__(self, engine_module: ModuleType, model: str, extract_audio_only: bool):
        self.engine_module = engine_module
        logger.status(f"Using Whisper module: {self.engine_module.__name__}")
        self.extract_audio_only = extract_audio_only

        try:
            self.whisper_model = self.engine_module.load_model(model, in_memory=True)
        except torch.cuda.OutOfMemoryError:
            print(Fore.YELLOW + "Not enough GPU memory. Switching to CPU. This will be much slower!" + Style.RESET_ALL)
            self.whisper_model = whisper.load_model(model, "cpu", in_memory=True)

    def generate(self, video_path: Path, overwrite: bool = False, verbose: bool = False, index: int = None, out_of: int = None,
                 audio_extraction: AudioExtractionMethod = AudioExtractionMethod.MoviePy):
        subtitle_path = video_path.parent / f"{video_path.stem}.en.vtt"
        alt_subtitle_path = video_path.parent / f"{video_path.stem}.vtt"

        prefix = f"[{index} / {out_of}] "

        if subtitle_path.exists() and not overwrite:
            logger.status(f"Skipping [exists]", value=video_path, prefix=prefix)
            return

        if alt_subtitle_path.exists() and not overwrite:
            if not subtitle_path.exists():
                subtitle_path = alt_subtitle_path

            logger.status(f"Skipping [alt-exists]", value=video_path, prefix=prefix)
            return

        logger.status(f"Generating Subtitles for", value=video_path, prefix=prefix)

        try:
            audio_path = extracted_audio_moviepy(video_path)
        except Exception as e_moviepy:
            logger.error(f"Failed generation with moviepy. Trying with ffmpeg", value=video_path)
            logger.warning(f"  - {e_moviepy}")
            try:
                audio_path = extracted_audio_ffmpeg(video_path)
                assert audio_path
            except Exception as e_ffmpeg:
                logger.error(f"Failed generation with ffmpeg", value=video_path)
                logger.warning(f"  - {e_ffmpeg}")
                return

        if self.extract_audio_only:
            return

        logger.status(f"Generating SRT File", value=subtitle_path)
        result = self.whisper_model.transcribe(str(audio_path), verbose=verbose, language="en", vad=True, vad_threshold=0.35)

        def _format_timedelta(td: timedelta) -> str:
            total_seconds = td.total_seconds()
            hours, remainder = divmod(int(total_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            milliseconds = int((total_seconds - int(total_seconds)) * 1000)
            return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

        # classic whisper requires us to generate the SRT manually
        vtt = webvtt.WebVTT()
        vtt.styles.append(webvtt.Style(
            """::cue {
    color: #fff;
    background: transparent;
    text-shadow: 0 0 2px #000, 0 0 4px #000;
}"""))
        for idx, segment in enumerate(result.segments):
            vtt.captions.append(webvtt.Caption(
                _format_timedelta(timedelta(seconds=segment.start)),
                _format_timedelta(timedelta(seconds=segment.end)),
                segment.text.strip(),
            ))

        vtt.save(str(subtitle_path))


class GenSubsTool(NaqTool):

    def _populate_parser(self):
        self.parser.add_argument("search_paths", type=Path, nargs="+")
        self.parser.add_argument("--module", choices=["whisper", "stable-whisper"], default="stable-whisper",
                            help="Default: %(default)s")
        self.parser.add_argument("--model", default="large-v3",
                            choices=whisper.available_models(),
                            help="Choose model if using whisper. Default: %(default)s", )
        self.parser.add_argument("--audio-extraction",
                            choices=[AudioExtractionMethod.MoviePy.value, AudioExtractionMethod.FFMPEG.value],
                            default=AudioExtractionMethod.MoviePy)
        self.parser.add_argument("--extract-audio-only", default=False, action="store_true")
        self.parser.add_argument("--overwrite", default=False, action="store_true")
        self.parser.add_argument("--verbose", default=False, action="store_true")
        self.parser.add_argument("--dry-run", action="store_true", default=False, help="Dry run. Make no changes.")
        self.parser.add_argument("--skip-if-embedded", action="store_true", default=False,
                            help="If set, will skip videos that have embedded subtitles")
        self.parser.add_argument("--quit-after", type=int, default=None, help="Quit after specified number of seconds.")

    def main(self, args: argparse.Namespace):
        import logging
        
        # Configure logging based on the parsed argument
        logger.setLevel(getattr(logging, args.log_level))

        try:
            import torch
        except ImportError:
            logger.error("You do not appear to have CUDA installed. Check README for instructions")
            sys.exit(1)

        generator = SubtitleGenerator(whisper if args.module == "whisper" else stable_whisper, args.model,
                                args.extract_audio_only) if not args.dry_run else None

        extensions = ("*.mkv", "*.mp4", "*.avi", "*.m4v")

        all_paths = []
        if args.search_paths:
            for path in args.search_paths:
                if path.is_dir():
                    print(f"Searching in: {path}")
                    for ext in extensions:
                        path = Path(path).absolute()
                        all_paths.extend(path.rglob(ext))
                elif path.is_file():
                    print(f"Generating subtitles for '{path}'")
                    all_paths.append(path)
        else:
            for ext in extensions:
                all_paths.extend(Path.cwd().rglob(ext))

        start = time.time()

        try:
            for idx, path in enumerate(sorted(all_paths, key=lambda x: str(x).lower())):
                if args.skip_if_embedded and has_subtitles(path):
                    continue

                if not args.dry_run and generator is not None:
                    generator.generate(
                        path,
                        overwrite=args.overwrite,
                        verbose=args.verbose,
                        audio_extraction=AudioExtractionMethod(args.audio_extraction),
                        index=idx+1,
                        out_of=len(all_paths)
                    )

                if args.quit_after and time.time() - start > args.quit_after:
                    logger.warning(f" Exiting after {args.quit_after} seconds.")
                    break

        except KeyboardInterrupt:
            pass


def main():
    import logging

    parser = argparse.ArgumentParser(description="Generate subtitles for video files using Whisper or Stable Whisper.")

    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                            default='WARNING', help='Set the logging level')
    
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.log_level.upper()))

    GenSubsTool(parser).main(args)


if __name__ == "__main__":
    main()
    