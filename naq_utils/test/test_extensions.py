from naq_utils.extensions import Path
import tempfile
import pathlib


class TestPath:
    
    def test_path_existsi(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            test_file = tmp_dir / "BOB"
            assert not test_file.exists()
            assert not test_file.existsi()

            test_file.touch()
            lowered_path = tmp_dir / "bob"
            assert not lowered_path.exists()
            assert lowered_path.existsi()
    