## yt-dlp passthrough

For downloader commands, put yt-dlp options after `--`. They are forwarded to
each yt-dlp download invocation. For example, to use browser cookies:

```sh
naq-toolbox downloader video VIDEO_URL -- --cookies-from-browser firefox
```

The same passthrough works with the standalone downloader command:

```sh
naq-video-downloader video VIDEO_URL -- --cookies-from-browser firefox
```

## Chaptered audio albums

For a YouTube video that contains an album with chapters, use the
`audio-album` command to extract one MP3 file for each chapter, named like
`01 - Track Name.mp3`. This mode does not need API keys or music metadata
lookups.

```sh
naq-toolbox downloader audio-album --download-dir ~/Music ALBUM_URL
```

Use `album` instead when you want separate MP4 files containing both video and
audio for each chapter:

```sh
naq-toolbox downloader album --download-dir ~/Videos ALBUM_URL
```
