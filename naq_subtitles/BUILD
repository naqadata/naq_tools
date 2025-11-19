load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@rules_python//python:packaging.bzl", "py_wheel")

exports_files(
    ["requirements.txt"],
    visibility = ["//:__pkg__"],
)

py_library(
    name = "convert_subtitles",
    srcs = ["convert_subtitles.py"],
    visibility = [
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
    ],
    deps = ["//naq_utils:naq_tool"],
)

py_library(
    name = "generate_subtitles",
    srcs = ["generate_subtitles.py"],
    visibility = [
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
    ],
    deps = [
        requirement("whisperx"),
        requirement("triton"),
        requirement("stable-ts"),
        requirement("moviepy"),
        requirement("colorama"),
        requirement("packaging"),
        requirement("webvtt-py"),
        "//naq_utils:logging",
        "//naq_utils:naq_tool",
    ],
)

py_binary(
    name = "naq_subtitles",
    srcs = ["__main__.py"],
    main = "__main__.py",
    visibility = [
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
    ],
    deps = [
        ":convert_subtitles",
        ":generate_subtitles",
        ":rename_videos_and_subtitles",
        "//naq_utils:console",
        "//naq_utils:logging",
        "//naq_utils:naq_tool",
    ],
)

py_library(
    name = "rename_videos_and_subtitles",
    srcs = ["rename_videos_and_subtitles.py"],
    visibility = [
        "//naq_subtitles/test:__pkg__",
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
    ],
    deps = [
        "//naq_utils:logging",
        "//naq_utils:naq_tool",
        "//naq_utils:extensions",
    ],
)

py_wheel(
    name = "naq_subtitles.wheel",
    distribution = "naq_subtitles",
    entry_points = {
        "console_scripts": ["naq_subtitles = naq_subtitles.__main__:main"],
    },
    requires_file = ":requirements.txt",
    version = "1.0",
    visibility = ["//release:__pkg__"],
    deps = [
        ":convert_subtitles",
        ":generate_subtitles",
        ":naq_subtitles",
        ":rename_videos_and_subtitles",
    ],
)
