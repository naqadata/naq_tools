Naqadata Tools
=========

This repository contains tools and utilities for video downloads, subtitle work, and helper libraries. It is a standard Python package: Bazel is not required.

Quick table of contents
- Installing and running
- Running tests
- Building a wheel
- Running `naq_toolbox` (CLI)

Installing and running
----------------------

Create a virtual environment and install a tagged release from GitHub:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install "git+https://github.com/naqadata/naq_tools.git@main"
naq-toolbox --help
```

For subtitle generation, install the optional AI dependencies (which can be large and may require system GPU/CUDA setup):

```bash
python -m pip install "naq-toolbox[subtitles] @ git+https://github.com/naqadata/naq_tools.git@main"
```

The CLI commands are `naq-toolbox`, `naq-video-downloader`, and `naq-subtitles`.

Feature Modules
---------------

- __naq_utils__ - utility modules such as logging and base class for Tools
- __naq_subtitles__ - Tool module that provides subtitle operations: AI generation, renaming, etc
  - See Subtitles [README](naq_subtitles/README.md) for further details
- __naq_video_downloader__ - Tool module that provides downloading ability from YouTube, Tubi, and others
  - See Downloader [README](naq_video_downloader/README.md) for further details
- __naq_toolbox__ - Module intended as top-level entry-point, bringing all Tool modules together
  - See Toolbox [README](naq_toolbox/README.md) for further details


Running tests
-------------

Install development dependencies and run all tests:

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

Building a wheel
----------------

```bash
python -m pip install build
python -m build
```

Running `naq_toolbox` (examples)
--------------------------------

Show `naq_toolbox` help:

```bash
naq-toolbox --help
```

Run the downloader subcommand:

```bash
naq-toolbox downloader video VIDEO_URL
```

Extract a chaptered album video into individual MP3 tracks without API keys:

```bash
naq-toolbox downloader audio-album --download-dir ~/Music ALBUM_URL
```

Use `album` rather than `audio-album` to split the source into MP4 files with
both video and audio.

If you build and install the wheels (or install from PyPI if published), the package exposes console scripts:

- `naq-toolbox` (toolbox package entrypoint)

After installing with pip, run:

```bash
naq-toolbox downloader --help
```

Developer notes & tips
----------------------

- Install from a commit SHA or version tag for reproducible deployments.
- `yt-dlp` is installed as a normal dependency and updated with `pip install --upgrade yt-dlp`.

Contacts / Next steps
---------------------

If you want, I can also:
- Add a short example showing a real downloader invocation (with safe sample args)
- Add a small CONTRIBUTING.md with development workflow

