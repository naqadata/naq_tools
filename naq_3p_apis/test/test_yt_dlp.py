import errno
from types import SimpleNamespace

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3

from naq_3p_apis.yt_dlp import YT_DLP


def test_download_forwards_cli_passthrough_args(monkeypatch, tmp_path):
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(YT_DLP, "extra_args", ("--cookies-from-browser", "firefox"))
    monkeypatch.setattr("naq_3p_apis.yt_dlp.subprocess.run", fake_run)

    YT_DLP.download("https://example.com/video", tmp_path / "video.mp4")

    command = commands[0]
    assert command[-3:] == ["--cookies-from-browser", "firefox", "https://example.com/video"]


def test_download_does_not_include_passthrough_args_by_default(monkeypatch, tmp_path):
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(YT_DLP, "extra_args", ())
    monkeypatch.setattr("naq_3p_apis.yt_dlp.subprocess.run", fake_run)

    YT_DLP.download("https://example.com/video", tmp_path / "video.mp4")

    assert commands[0][-1] == "https://example.com/video"
    assert "--cookies-from-browser" not in commands[0]


def test_download_audio_chapters_requests_mp3_for_each_chapter(monkeypatch, tmp_path):
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("naq_3p_apis.yt_dlp.subprocess.run", fake_run)

    YT_DLP.download_audio_chapters(
        "https://example.com/album",
        tmp_path,
        artist="Artist",
        album="Album",
    )

    command = commands[0]
    assert "--split-chapters" in command
    assert command[command.index("--audio-format") + 1] == "mp3"
    assert "bestvideo+bestaudio/best" not in command
    output_templates = [
        command[index + 1]
        for index, value in enumerate(command)
        if value == "--output"
    ]
    assert output_templates == [
        ".naq-source-%(id)s.%(ext)s",
        "chapter:%(section_number)02d - %(section_title)s.%(ext)s",
    ]


def test_download_chapters_discards_full_album_source(monkeypatch, tmp_path):
    def fake_run(cmd, **kwargs):
        temp_dir = kwargs["cwd"]
        (temp_dir / ".naq-source-video-id.mp3").write_bytes(b"full album")
        (temp_dir / "01 - Chapter One.mp3").write_bytes(b"chapter")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("naq_3p_apis.yt_dlp.subprocess.run", fake_run)
    tagged_files = []
    monkeypatch.setattr(
        YT_DLP,
        "_write_audio_metadata",
        lambda path, artist, album: tagged_files.append((path.name, artist, album)),
    )

    downloaded = YT_DLP.download_audio_chapters(
        "https://example.com/album",
        tmp_path,
        artist="Artist",
        album="Album",
    )

    assert [path.name for path in downloaded] == ["01 - Chapter One.mp3"]
    assert (tmp_path / "01 - Chapter One.mp3").read_bytes() == b"chapter"
    assert not (tmp_path / ".naq-source-video-id.mp3").exists()
    assert tagged_files == [("01 - Chapter One.mp3", "Artist", "Album")]


def test_write_audio_metadata_sets_windows_media_player_fields(tmp_path):
    chapter = tmp_path / "01 - Chapter One.mp3"
    ID3().save(chapter)

    YT_DLP._write_audio_metadata(chapter, artist="Artist", album="Album")

    tags = EasyID3(chapter)
    assert tags["title"] == ["Chapter One"]
    assert tags["artist"] == ["Artist"]
    assert tags["album"] == ["Album"]
    assert tags["tracknumber"] == ["01"]


def test_move_downloaded_file_copies_contents_after_cross_device_error(monkeypatch, tmp_path):
    source = tmp_path / "source.mp4"
    destination = tmp_path / "destination.mp4"
    source.write_bytes(b"video bytes")

    def raise_cross_device_error(*args):
        raise OSError(errno.EXDEV, "Invalid cross-device link")

    monkeypatch.setattr("naq_3p_apis.yt_dlp.os.replace", raise_cross_device_error)

    YT_DLP._move_downloaded_file(source, destination)

    assert destination.read_bytes() == b"video bytes"
    assert not source.exists()
