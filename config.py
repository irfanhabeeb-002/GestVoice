import os
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()
from logger import log


@dataclass
class Settings:
    whisper_api_key: str
    base_folder_path: str
    homepage_url: str
    sarvam_api_key: str = ""

def get_settings() -> Settings:
    home = os.path.expanduser("~")
    desktop = os.path.join(home, "Desktop")

    return Settings(
        whisper_api_key=os.getenv("WHISPER_API_KEY", ""),
        sarvam_api_key=os.getenv("SARVAM_API_KEY", ""),
        base_folder_path=os.getenv("GV_BASE_FOLDER", os.path.join(desktop, "GestVoice")),
        homepage_url=os.getenv("GV_HOMEPAGE_URL", "https://www.google.com"),
    )