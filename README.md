NAQADATA Tools
=========

This repository contains tools and utilities (downloaders, subtitle tooling, and helper libraries). The project uses Bazel for builds, tests, and packaging.

Quick table of contents
- Building & running locally with Bazel
- Running tests
- Building wheels & bundles
- Release packaging
- Running `naq_toolbox` (CLI)

Building & running locally with Bazel
------------------------------------

Run the `naq_toolbox` package directly (its own py_binary):

```bash
# Run the toolbox package and pass args after --
bazel run //naq_toolbox:naq_toolbox -- <subcommand> [args]
```

Notes:
- Use `--` to separate Bazel args from the program args. For example:
  `bazel run //naq_toolbox:naq_toolbox -- downloader --log-level DEBUG`
- The toolbox and top-level entrypoints provide subcommands; the main available subcommands are `downloader` and `subtitles` (when subtitle support is available).

Running tests
-------------

Run all pytests in the repository:

```bash
bazel test //... --test_tag_filters=pytest
```

To run a single package's tests, target that package instead (example):

```bash
bazel test //naq_utils/... --test_tag_filters=pytest
```

Building wheels & local packaging
---------------------------------

Several Python wheel targets are provided across the repo. Example wheel targets:

- `naq_toolbox` wheel: `//naq_toolbox:naq_toolbox.wheel`
- `naq_utils` wheel: `//naq_utils:naq_utils.wheel`

Build a wheel with:

```bash
bazel build //naq_toolbox:naq_toolbox.wheel
bazel build //naq_utils:naq_utils.wheel
```

A convenience bundle (tar/zip) is also defined under the top-level `BUILD`/`release` packages that gather wheels from components.

Release packaging
-----------------

The `release` package contains helpers to produce zip/pyzip installers for the `naq_toolbox` application.

Build the generated pyzip/executable for the `naq_toolbox` release:

```bash
# Build the generated pyzip target (buggy, very large)
bazel build //release:naq_toolbox.pyzip

# The output executable will be in bazel-bin/release/naq_toolbox
# You can run it directly:
./bazel-bin/release/naq_toolbox
```

There is also an install helper py_binary generated as `naq_toolbox.install`; you can run it directly with Bazel:

```bash
bazel run //release:naq_toolbox.install -- [install-args]
```

This will copy the naq_toolbox entry script and .runfiles directory to /usr/local/bin

(Exact install behaviour depends on the `release/install.py` script in the `release` package.)

Running `naq_toolbox` (examples)
--------------------------------

Show `naq_toolbox` help:

```bash
bazel run //naq_toolbox:naq_toolbox -- --help
```

Run the downloader subcommand:

```bash
bazel run //naq_toolbox:naq_toolbox -- downloader --log-level INFO
```

If you build and install the wheels (or install from PyPI if published), the package exposes console scripts:

- `naq_toolbox` (toolbox package entrypoint)

After installing with pip, run:

```bash
naq_toolbox downloader --help
```

Developer notes & tips
----------------------

- To see failing test output inline, use `--test_output=errors` with `bazel test`.
- Build artifacts from Bazel are under `bazel-bin/`.
- The repository pins Python requirements for 3.12 in Bazel; ensure you run Bazel with an appropriate Python toolchain if you need to reproduce packaging/build steps locally.

Contacts / Next steps
---------------------

If you want, I can also:
- Add a short example showing a real downloader invocation (with safe sample args)
- Add a small CONTRIBUTING.md with development workflow

