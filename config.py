import os
from dataclasses import dataclass

from dotenv import load_dotenv
from logger import log

load_dotenv()


@dataclass
class Settings:
    whisper_api_key: str
    base_folder_path: str
    homepage_url: str


def get_settings() -> Settings:
    """
    Load configuration from environment variables with sensible defaults.
    """
    home = os.path.expanduser("~")
    desktop = os.path.join(home, "Desktop")

    whisper_api_key = os.environ.get("WHISPER_API_KEY", "")
    base_folder_path = os.environ.get("GV_BASE_FOLDER", os.path.join(desktop, "GestVoice"))
    homepage_url = os.environ.get("GV_HOMEPAGE_URL", "https://www.google.com")

    return Settings(
        whisper_api_key=whisper_api_key,
        base_folder_path=base_folder_path,
        homepage_url=homepage_url,
    )

