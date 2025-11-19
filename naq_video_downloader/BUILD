load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@rules_python//python:packaging.bzl", "py_wheel")

exports_files(
    ["requirements.txt"],
    visibility = ["//:__pkg__"],
)

py_library(
    name = "settings",
    srcs = ["settings.py"],
    deps = [
        "//naq_utils:settings",
    ],
)

py_library(
    name = "youtube_video",
    srcs = ["youtube_video.py"],
    deps = [
        requirement("python-youtube"),
        "//naq_3p_apis:youtube_api",
        "//naq_utils:extensions",
        "//naq_utils:logging",
        "//naq_utils:serialize",
        "//naq_video_downloader:settings",
    ],
    visibility = ["//naq_video_downloader/test:__pkg__"]
)

py_library(
    name = "youtube_music_video",
    srcs = ["youtube_music_video.py"],
    deps = [
        requirement("python-youtube"),
        "//naq_3p_apis:http",
        "//naq_3p_apis:imvdb",
        "//naq_3p_apis:theaudiodb",
        "//naq_utils:logging",
        "//naq_utils:extensions",
        "//naq_video_downloader:settings",
        "//naq_video_downloader:youtube_video",
    ],
    visibility = ["//naq_video_downloader/test:__pkg__"]
)

py_binary(
    name = "naq_video_downloader",
    srcs = ["__main__.py"],
    main = "__main__.py",
    deps = [
        requirement("emoji"),
        requirement("python-youtube"),
        "//naq_3p_apis:youtube_api",
        "//naq_utils:extensions",
        "//naq_utils:logging",
        "//naq_utils:naq_tool",
        "//naq_video_downloader:youtube_music_video",
        "//naq_video_downloader:settings",
    ],
    visibility = [
        "//naq_toolbox:__pkg__",
        "//release:__pkg__",
    ],
)

py_wheel(
    name = "naq_video_downloader.wheel",
    distribution = "naq_video_downloader",
    entry_points = {
        "console_scripts": [
            "naq_video_downloader = naq_video_downloader.__main__:main",
        ],
    },
    requires_file = ":requirements.txt",
    version = "1.0",
    visibility = ["//release:__pkg__"],
    deps = [
        ":naq_video_downloader",
        ":settings",
        ":youtube_music_video",
        ":youtube_video",
    ],
)
