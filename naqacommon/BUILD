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
