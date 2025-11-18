load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")
load("@rules_python//python:packaging.bzl", "py_wheel")

exports_files(["requirements.txt"], visibility = ["//:__pkg__"])

py_library(
    name = "console",
    srcs = ["console.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "constants",
    srcs = ["constants.py"],
    deps = [":extensions"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "extensions",
    srcs = ["extensions.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "logging",
    srcs = ["logging.py"],
    deps = [
        requirement("colorama"),
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "naq_tool",
    srcs = ["naq_tool.py"],
    visibility = ["//visibility:public"],
)

py_wheel(
    name = "naq_utils.wheel",
    distribution = "naq_utils",
    version = "1.0",
    deps = [
        ":console",
        ":logging",
        ":naq_tool",
    ],
    requires_file = ":requirements.txt",
    visibility = ["//release:__pkg__"],
)

py_library(
    name = "serialize",
    srcs = ["serialize.py"],
    deps = [":constants"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "settings",
    srcs = ["settings.py"],
    deps = [
        requirement("shared-memory-dict"),
        ":constants",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "caching",
    srcs = ["caching.py"],
    deps = [
        ":constants",
    ],
    visibility = ["//visibility:public"],
)