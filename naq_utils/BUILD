load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")
load("@rules_python//python:packaging.bzl", "py_wheel")

exports_files(
    ["requirements.txt"],
    visibility = ["//:__pkg__"],
)

py_library(
    name = "caching",
    srcs = ["caching.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":constants",
    ],
)

py_library(
    name = "console",
    srcs = ["console.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "constants",
    srcs = ["constants.py"],
    visibility = ["//visibility:public"],
    deps = [":extensions"],
)

py_library(
    name = "extensions",
    srcs = ["extensions.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "logging",
    srcs = ["logging.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("colorama"),
    ],
)

py_library(
    name = "naq_tool",
    srcs = ["naq_tool.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "serialize",
    srcs = ["serialize.py"],
    visibility = ["//visibility:public"],
    deps = [":constants"],
)

py_library(
    name = "settings",
    srcs = ["settings.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("shared-memory-dict"),
        ":constants",
    ],
)

py_wheel(
    name = "naq_utils.wheel",
    distribution = "naq_utils",
    requires_file = ":requirements.txt",
    version = "1.0",
    visibility = ["//release:__pkg__"],
    deps = [
        ":caching",
        ":console",
        ":constants",
        ":extensions",
        ":logging",
        ":naq_tool",
        ":serialize",
        ":settings",
    ],
)
