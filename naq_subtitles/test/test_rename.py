import pytest
from pathlib import Path
import tempfile
from naq_subtitles.rename_videos_and_subtitles import File, EpisodeFiles, FileMap
from dataclasses import dataclass
from typing import Generator


@dataclass
class TempSeason:
    show_name: str
    season_num: int
    num_episodes: int
    path: Path

    def __iter__(self) -> Generator[File, None, None]:
        for file in File.from_root_dir(self.path):
            yield file

    def get_episode_files(self, episode_num: int) -> tuple[File|None, File|None]:
        video_file = None
        subtitle_file = None

        ep_tag = f"S{self.season_num:02}E{episode_num:02}"

        for file in self:
            if file.is_supported_video() and file.episode_tag == ep_tag: video_file = file
            elif file.is_supported_subtitles() and file.episode_tag == ep_tag: subtitle_file = file

            if video_file and subtitle_file:
                return video_file, subtitle_file

        return None, None

@pytest.fixture()
def temp_season():
    with tempfile.TemporaryDirectory() as tmp_dir_str:            
        show_name = "My Show Name"
        season_num = 1
        num_episodes = 10

        tmp_dir = Path(tmp_dir_str)
        show_dir = tmp_dir / show_name
        season_dir = show_dir / f"season.{season_num}"

        season_dir.mkdir(parents=True)

        for i in range(1, num_episodes+1):
            vid_path = season_dir / f"Some kind of text Series {season_num} Episode {i}.mp4"
            vtt_path = season_dir / f"Other noise in the name with diff format {season_num}x{i}.vtt"

            vid_path.touch()
            vtt_path.touch()

        yield TempSeason(show_name, season_num, num_episodes, season_dir)


class TestRename_File:
    def test_from_root_dir(self, temp_season: TempSeason):
        files = list(File.from_root_dir(temp_season.path))

        assert len(files) == temp_season.num_episodes * 2

        num_videos = 0
        num_subtitles = 0

        ep_tags = []

        for file in temp_season:
            assert file
            assert file.episode_tag

            ep_tags.append(file.episode_tag)

            if file.is_supported_video(): num_videos += 1
            elif file.is_supported_subtitles(): num_subtitles += 1

        assert ep_tags == sorted(ep_tags)

        assert num_videos == temp_season.num_episodes
        assert num_subtitles == temp_season.num_episodes

    def test_episode_files(self, temp_season: TempSeason):
        vid, sub = temp_season.get_episode_files(1)
        assert vid and sub

        episode_files = EpisodeFiles()
        episode_files.set(vid)

        assert episode_files.video == vid
        assert episode_files.subtitles is None

        episode_files.set(sub)
        
        assert episode_files.subtitles == sub
        assert episode_files.video == vid
    
    def test_file_map(self, temp_season: TempSeason):
        file_map = FileMap()
        
        assert len(file_map._map.items()) == 0
        assert len(file_map._renames.items()) == 0

        for file in temp_season:
            file_map.add(file)

        assert len(file_map._map.items()) > 0
        assert len(file_map._renames.items()) > 0

    def test_rename(self, temp_season: TempSeason):
        file_map = FileMap()
        original_names = []

        for file in temp_season:
            file_map.add(file)
            original_names.append(file.path.name)

        file_map.execute_renames()

        for file in temp_season:
            assert file.episode_tag
            assert file.path.name not in original_names
            assert file.path.name.startswith(temp_season.show_name)
            assert file.path.name.split(".")[0].endswith(file.episode_tag)

    def test_rename_with_overrides(self, temp_season: TempSeason):
        file_map = FileMap()

        for file in File.from_root_dir(temp_season.path, season_num=5, starting_ep_num=10):
            assert file.episode_tag
            season_num, episode_num = file.parse_episode_tag()
            assert season_num and episode_num
            assert season_num == 5
            assert episode_num >= 10
