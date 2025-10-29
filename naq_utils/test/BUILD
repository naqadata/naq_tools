load("//test_drivers:test_runners.bzl", "pytest_test")
load("@pypi//:requirements.bzl", "requirement")

pytest_test(
    name = "test_console",
    test = "test_console.py",
    deps = [
        requirement("colorama"),
        "//naq_utils:console",
    ],
)