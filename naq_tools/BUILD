load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "naq_tools",
    srcs = ["naq_tools.py"],
    main = "naq_tools.py",
    deps = [
        "//web_video_downloader:web_video_downloader",
        "//video_utils:rename_with_subtitles",
    ],
    visibility = ["//release:__pkg__"],
)