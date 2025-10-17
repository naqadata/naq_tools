load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_binary")


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

py_library(
    name = "plex",
    srcs = ["plex.py"],
    deps = [
        requirement("plexapi"),
        "//naq_utils:console",
        "//naq_utils:custom_logging",
        ":exceptions",
        ":media_server",
        ":theaudiodb",
        ":utils",
    ],
)

py_binary(
    name = "web_video_downloader",
    srcs =["__main__.py"],
    main = "__main__.py",
    deps = [
        requirement("emoji"),
        "//naq_utils:naq_tool",
        "//naq_utils:custom_logging",
        "//naq_utils:console",
        ":youtube_api",
        ":plex",
        ":video",
    ],
    visibility = [
        "//release:__pkg__",
        "//:__pkg__",
    ],
)

