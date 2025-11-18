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

pytest_test(
    name = "test_extensions",
    test = "test_extensions.py",
    deps = [
        requirement("shared-memory-dict"),
        "//naq_utils:extensions",
    ],
)

pytest_test(
    name = "test_logging",
    test = "test_logging.py",
    deps = [
        requirement("colorama"),
        "//naq_utils:logging",
    ],
)

pytest_test(
    name = "test_settings",
    test = "test_settings.py",
    deps = [
        requirement("shared-memory-dict"),
        "//naq_utils:settings",
    ],
)