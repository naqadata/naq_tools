load("@pypi//:requirements.bzl", "requirement")
load("//test_drivers:test_runners.bzl", "pytest_test")

pytest_test(
    name = "test_youtube_video",
    test = "test_youtube_video.py",
    deps = [
        requirement("python-youtube"),
        "//naq_video_downloader:youtube_video",
    ],
)

pytest_test(
    name = "test_youtube_music_video",
    test = "test_youtube_music_video.py",
    deps = [
        requirement("python-youtube"),
        "//naq_video_downloader:youtube_music_video",
    ],
)
