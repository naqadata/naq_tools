# Make requirements.txt addressable as //:requirements.txt
load("@rules_python//python:defs.bzl", "py_binary")
load("@rules_python//python:packaging.bzl", "py_wheel")

filegroup(
    name = "naq_toolbox_src",
    srcs = glob(["*.py"]),
)

py_binary(
    name = "naq_toolbox",
    srcs = [":naq_toolbox_src"],
    main = "__main__.py",
    deps = [
        "//naq_video_downloader:naq_video_downloader",
        "//naq_subtitles:naq_subtitles",
    ],
    visibility = ["//release:__pkg__"],
)

py_wheel(
    name = "naq_toolbox.wheel",
    distribution = "naq_toolbox",
    version = "1.0",
    deps = [":naq_toolbox_src"],
    entry_points = {
        "console_scripts": [
            "naq_toolbox = naq_toolbox.__main__:main",
        ],
    },
    visibility = ["//release:__pkg__"],
)