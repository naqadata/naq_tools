load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@rules_python//python:packaging.bzl", "py_wheel")

py_library(
    name = "api",
    srcs = ["api.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("urllib3"),
        "//naq_utils:caching",
        "//naq_utils:logging",
    ],
)

py_library(
    name = "exceptions",
    srcs = ["exceptions.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "http",
    srcs = ["http.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("urllib3"),
    ],
)

py_library(
    name = "imvdb",
    srcs = ["imvdb.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("urllib3"),
        ":api",
        "//naq_utils:caching",
        "//naq_utils:logging",
    ],
)

py_library(
    name = "theaudiodb",
    srcs = ["theaudiodb.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("urllib3"),
        ":exceptions",
        "//naq_utils:caching",
        "//naq_utils:logging",
        "//naq_utils:settings",
    ],
)

py_library(
    name = "youtube_api",
    srcs = ["youtube_api.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("python-youtube"),
        requirement("emoji"),
        ":yt_dlp",
        "//naq_utils:caching",
        "//naq_utils:logging",
        "//naq_utils:settings",
    ],
)

py_library(
    name = "yt_dlp",
    srcs = ["yt_dlp.py"],
    data = [":yt-dlp"],
    deps = [
        "//naq_utils:logging",
    ],
)
