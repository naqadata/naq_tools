load("@pypi//:requirements.bzl", "requirement")
load("//test_drivers:test_runners.bzl", "pytest_test")

pytest_test(
    name = "test_youtube_api",
    test = "test_youtube_api.py",
    deps = [
        requirement("python-youtube"),
        "//naq_3p_apis:youtube_api",
    ],
)

pytest_test(
    name = "test_yt_dlp",
    test = "test_yt_dlp.py",
    deps = ["//naq_3p_apis:yt_dlp"],
)
