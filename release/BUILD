load("//release:defs.bzl", "naq_release")
load("@rules_pkg//pkg/private/zip:zip.bzl", "pkg_zip")


exports_files(["requirements.txt"], visibility = ["//:__pkg__"])

naq_release(
    name = "naq_toolbox",
    app_target = "//naq_toolbox:naq_toolbox",
)

pkg_zip(
    name = "naq_tools.bundle",
    out = "naq_tools_bundle.zip",
    srcs = [
        "//naq_toolbox:naq_toolbox.wheel",
        "//naq_utils:naq_utils.wheel",
        "//naq_subtitles:naq_subtitles.wheel",
        "//naq_video_downloader:naq_video_downloader.wheel",
    ],
)