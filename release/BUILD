load("@rules_pkg//pkg/private/zip:zip.bzl", "pkg_zip")
load("//naq_utils:defs.bzl", "naq_release")

exports_files(
    ["requirements.txt"],
    visibility = ["//:__pkg__"],
)

naq_release(
    name = "naq_toolbox",
    app_target = "//naq_toolbox",
)

pkg_zip(
    name = "naq_toolbox.wheels",
    srcs = [
        "//naq_3p_apis:naq_3p_apis.wheel",
        "//naq_subtitles:naq_subtitles.wheel",
        "//naq_toolbox:naq_toolbox.wheel",
        "//naq_utils:naq_utils.wheel",
        "//naq_video_downloader:naq_video_downloader.wheel",
    ],
    out = "naq_toolbox_wheels.zip",
)
