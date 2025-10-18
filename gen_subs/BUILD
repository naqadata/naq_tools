load("@rules_python//python:defs.bzl", "py_binary")
load("@pypi//:requirements.bzl", "requirement")

py_binary(
    name = "gen_subs",
    srcs = ["gen_subs.py"],
    main = "gen_subs.py",
    deps = [
        requirement("openai-whisper"),
        requirement("triton"),
        requirement("stable-ts"),
        requirement("srt"),
        requirement("moviepy"),
        requirement("colorama"),
        "//naq_utils:naq_tool",
    ],
    visibility = [
        "//:__pkg__",
        "//release:__pkg__",
    ],
)
