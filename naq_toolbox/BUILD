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
    visibility = ["//release:__pkg__"],
    deps = [
        "//naq_subtitles",
        "//naq_video_downloader",
    ],
)

py_wheel(
    name = "naq_toolbox.wheel",
    distribution = "naq_toolbox",
    entry_points = {
        "console_scripts": [
            "naq_toolbox = naq_toolbox.__main__:main",
        ],
    },
    version = "1.0",
    visibility = ["//release:__pkg__"],
    deps = [":naq_toolbox"],
)
