load("@pypi//:requirements.bzl", "requirement")

py_library(
    name = "console",
    srcs = ["console.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "custom_logging",
    srcs = ["custom_logging.py"],
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