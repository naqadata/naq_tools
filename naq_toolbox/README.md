## yt-dlp passthrough

For downloader commands, put yt-dlp options after `--`. They are forwarded to
each yt-dlp download invocation. For example, to use browser cookies:

```sh
naq_toolbox downloader download targets VIDEO_URL -- --cookies-from-browser firefox
```

This also works through Bazel:

```sh
bazel run //naq_toolbox:naq_toolbox -- downloader download targets VIDEO_URL -- --cookies-from-browser firefox
```
