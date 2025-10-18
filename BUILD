# Make requirements.txt addressable as //:requirements.txt
exports_files(["requirements.txt", "setup.py"])
load("@python_versions//3.12:defs.bzl", compile_pip_requirements_3_12 = "compile_pip_requirements")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

compile_pip_requirements_3_12(
    name = "requirements_3_12",
    timeout = "moderate",
    src = "requirements.txt",
    requirements_txt = "requirements_lock_3_12.txt",
)

py_binary(
    name = "naq_tools",
    srcs = ["main.py"],
    main = "main.py",
    deps = [
        "//web_video_downloader:web_video_downloader",
        "//video_utils:rename_with_subtitles",
        "//gen_subs:gen_subs",
    ],
    visibility = ["//release:__pkg__"],
)