load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:packaging.bzl", "py_wheel")

exports_files(["requirements.txt"], visibility = ["//:__pkg__"])

py_binary(
    name = "generate_subtitles",
    srcs = ["generate_subtitles.py"],
    main = "generate_subtitles.py",
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
    visibility = [
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
    ],
)

py_library(
    name = "rename_videos_and_subtitles",
    srcs = ["rename_videos_and_subtitles.py"],
    deps = [
        "//naq_utils:naq_tool",
        "//naq_utils:logging",
    ],
    visibility = [
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
        "//naq_subtitles/test:__pkg__",
    ],
)

py_library(
    name = "convert_subtitles",
    srcs = ["convert_subtitles.py"],
    deps = ["//naq_utils:naq_tool"],
    visibility = [
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
    ],
)

py_binary(
    name = "naq_subtitles",
    srcs =["__main__.py"],
    main = "__main__.py",
    deps = [
        ":generate_subtitles",
        ":rename_videos_and_subtitles",
        ":convert_subtitles",
        "//naq_utils:naq_tool",
        "//naq_utils:logging",
        "//naq_utils:console",
    ],
    visibility = [
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
    ],
)

py_wheel(
    name = "naq_subtitles.wheel",
    distribution = "naq_subtitles",
    version = "1.0",
    deps = [
        ":generate_subtitles",
        ":rename_videos_and_subtitles",
        ":naq_subtitles",
    ],
    requires_file = ":requirements.txt",
    entry_points = {
        "console_scripts": ["naq_subtitles = naq_subtitles.__main__:main"]
    },
    visibility = ["//release:__pkg__"],
)