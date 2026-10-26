import errno
from types import SimpleNamespace

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
