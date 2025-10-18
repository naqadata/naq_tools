load("@rules_python//python:defs.bzl", "py_binary")
load("@pypi//:requirements.bzl", "requirement")

py_binary(
    name = "rename_with_subtitles",
    srcs = ["rename_with_subtitles.py"],
    main = "rename_with_subtitles.py",
    deps = [
        "//naq_utils:naq_tool",
    ],
    visibility = [
        "//:__pkg__",
        "//release:__pkg__",
    ],
)
