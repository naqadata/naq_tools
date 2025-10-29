#!/usr/bin/env python3
import argparse
import logging
import re
import tempfile
import shutil
import sys
import time
from typing import Optional
from pathlib import Path
from datetime import timedelta, datetime


def _get_datetime(text: str, with_ms: bool = False) -> datetime:
    fmt = "%H:%M:%S,%f" if with_ms else "%H:%M:%S"
    return datetime.strptime(text, fmt)


def _get_timedelta(text: str, with_ms: bool = False) -> timedelta:
    dt = _get_datetime(text, with_ms=with_ms)
    return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, milliseconds=int(dt.microsecond / 1000))


class Entry:
    def __init__(self, index: int):
        self.index: int = index
        self.start_time: Optional[timedelta] = None
        self.end_time: Optional[timedelta] = None
        self.text: str = ""

    def __repr__(self) -> str:
        return f"{self.index:03} [{self.start_str} - {self.end_str}]"

    @property
    def start_str(self) -> str:
        HHMMSS = time.strftime("%H:%M:%S", time.gmtime(self.start_time.total_seconds()))
        return f"{HHMMSS},{int(self.start_time.microseconds / 1000):03}"

    @property
    def end_str(self) -> str:
        HHMMSS = time.strftime("%H:%M:%S", time.gmtime(self.end_time.total_seconds()))
        return f"{HHMMSS},{int(self.end_time.microseconds / 1000):03}"

    def to_srt_format(self) -> str:
        return f"{self.index}\n{self.start_str} --> {self.end_str}\n{self.text}\n"

    def clone_with_offset(self, offset: timedelta) -> "Entry":
        new_entry = Entry(self.index)
        new_entry.text = self.text
        new_entry.start_time = self.start_time + offset
        new_entry.end_time = self.end_time + offset
        return new_entry

    def clone_with_scaling(self, scaling_factor: float) -> "Entry":
        new_entry = Entry(self.index)
        new_entry.text = self.text
        new_entry.start_time = self.start_time * scaling_factor
        new_entry.end_time = self.end_time * scaling_factor
        return new_entry


def resync_file(srt_path: Path, start_time: str, offset: int = None, scaling_factor: float = None, create_copy: bool = False):
    assert srt_path.exists() and srt_path.is_file()

    start_time = _get_timedelta(start_time)
    offset = timedelta(milliseconds=offset) if offset else None

    formats = ["utf-8-sig", "latin1"]
    entries = []
    current_entry = None
    for fmt in formats:
        try:
            with srt_path.open("r", encoding=fmt) as srt_file:
                for line in srt_file:
                    line = line.strip()
                    if not current_entry:
                        # if we have no current entry but encounter a blank line, skip it
                        if not line:
                            continue

                        current_entry = Entry(int(line))
                    elif current_entry.start_time is None:
                        result = re.match(r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", line)
                        current_entry.start_time = _get_timedelta(result.group(1), with_ms=True)
                        current_entry.end_time = _get_timedelta(result.group(2), with_ms=True)
                    elif line.strip():
                        current_entry.text += line
                    else:
                        entries.append(current_entry)
                        current_entry = None
            break
        except UnicodeDecodeError as e:
            logging.error(e)

    # resync the entries
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        tmp_file_path = tmp_dir / f"{srt_path.name}"
        with tmp_file_path.open("w") as tmp_file:
            for entry in entries:
                if entry.start_time >= start_time:
                    if scaling_factor:
                        resynced_entry = entry.clone_with_scaling(scaling_factor)
                    else:
                        resynced_entry = entry.clone_with_offset(offset)

                    logging.info(f"RESYNC: {entry}  --->  {resynced_entry}")
                    logging.debug(f"NEW ENTRY:\n{resynced_entry.to_srt_format()}")
                    tmp_file.write(resynced_entry.to_srt_format())
                else:
                    tmp_file.write(entry.to_srt_format())

        if create_copy:
            shutil.copy(tmp_file_path, srt_path.parent / f"{srt_path.name}.resync")
        else:
            shutil.copy(tmp_file_path, srt_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("srt_paths", nargs="+", help="Path of input SRT files to resync")
    parser.add_argument("--start-time", default="00:00:00",
                        help="Timestamp at which to start resync. Default: %(default)s")
    parser.add_argument("--copy", action="store_true", default=False, help="Save resync to new file")
    parser.add_argument("--scale", dest="scaling_factor", type=float,
                        help="amount by which to scale timestamps. Eg 1.0 = no change, 2.0 = double times, 0.5 = halve times")
    parser.add_argument("--offset", default=1000, type=int, help="Offset in milliseconds. Default: %(default)s")
    parser.add_argument("--info", action="store_true", default=False, help="Enable INFO logging")
    parser.add_argument("--debug", action="store_true", default=False, help="Enable DEBUG logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO if args.info else logging.WARNING)

    srt_paths = [Path(x) for x in args.srt_paths]

    print(f"SRT Files:")
    for srt_path in srt_paths:
        print(f"  - {srt_path.name}")
    print(f"Start Time: {args.start_time}")
    if args.scaling_factor:
        print(f"Scale by factor: {args.scaling_factor}")
    else:
        print(f"Offset: {args.offset}")
    print(f"In-place: {not args.copy}")

    input("\nPress enter to continue or Ctrl-C to quit")

    for srt_path in srt_paths:
        by_str = f"scaling factor of {args.scaling_factor}" if args.scaling_factor else f"{args.offset} ms"
        sys.stdout.write(f"Resyncing {srt_path} by {by_str}, starting at {args.start_time}... ")
        resync_file(srt_path, args.start_time, offset=args.offset, scaling_factor=args.scaling_factor, create_copy=args.copy)
        print("DONE")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n')
