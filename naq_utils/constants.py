from naq_utils.extensions import Path

HOME_SAVE_DIR = Path.home() / ".naq_tools"
HOME_SAVE_DIR.mkdir(exist_ok=True)