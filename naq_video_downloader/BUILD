load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_binary")
load("@rules_python//python:packaging.bzl", "py_wheel")

exports_files(["requirements.txt"], visibility = ["//:__pkg__"])

py_library(
    name = "utils",
    srcs = ["utils.py"],
    deps = [
        requirement("urllib3"),
        requirement("shared_memory_dict"),
    ],
)

py_library(
    name = "exceptions",
    srcs = ["exceptions.py"],
)

py_library(
    name = "manual_info",
    srcs = ["manual_info.py"],
    deps = [
        "//naq_utils:custom_logging",
        ":utils",
        ":exceptions",
    ],
)

py_library(
    name = "library_item",
    srcs = ["library_item.py"],
    deps = [
        ":utils",
    ],
)

py_library(
    name = "theaudiodb",
    srcs = ["theaudiodb.py"],
    deps = [
        requirement("urllib3"),
        ":utils",
        ":manual_info",
        ":exceptions",
    ],
)

py_library(
    name = "imvdb",
    srcs = ["imvdb.py"],
    deps = [
        requirement("urllib3"),
        "//naq_utils:custom_logging",
        ":utils",
    ],
)

py_library(
    name = "media_server",
    srcs = ["media_server.py"],
)

py_library(
    name = "artist",
    srcs = ["artist.py"],
    deps = [
        "//naq_utils:custom_logging",
        ":theaudiodb",
        ":utils",
        ":library_item",
    ],
)

py_library(
    name = "video",
    srcs = ["video.py"],
    deps = [
        "//naq_utils:custom_logging",
        ":artist",
        ":theaudiodb",
        ":exceptions",
        ":utils",
        ":library_item",
    ],
)

py_library(
    name = "youtube_api",
    srcs = ["youtube_api.py"],
    deps = [
        requirement("google-api-python-client"),
        "//naq_utils:custom_logging",
        ":video",
        ":utils",
        ":exceptions",
    ],
    data = [
        ":yt-dlp",
    ]
)

py_binary(
    name = "naq_video_downloader",
    srcs =["__main__.py"],
    main = "__main__.py",
    deps = [
        requirement("emoji"),
        "//naq_utils:naq_tool",
        "//naq_utils:custom_logging",
        "//naq_utils:console",
        ":youtube_api",
        ":video",
    ],
    visibility = [
        "//release:__pkg__",
        "//naq_toolbox:__pkg__",
    ],
)

filegroup(
    name = "downloader_binaries",
    srcs = [":yt-dlp"],
)

py_wheel(
    name = "naq_video_downloader.wheel",
    distribution = "naq_video_downloader",
    version = "1.0",
    deps = [
        ":naq_video_downloader",
        ":artist",
        ":exceptions",
        ":imvdb",
        ":library_item",
        ":manual_info",
        ":media_server",
        ":theaudiodb",
        ":utils",
        ":video",
        ":youtube_api",
        ":downloader_binaries",
    ],
    requires_file = ":requirements.txt",
    entry_points = {
        "console_scripts": [
            "naq_video_downloader = naq_video_downloader.__main__:main",
        ],
    },
    visibility = ["//release:__pkg__"],
)
