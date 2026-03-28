from __future__ import annotations
from datetime import datetime
from config import get_settings
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


class IntentName:
    SET_BRIGHTNESS = "SET_BRIGHTNESS"
    SET_VOLUME = "SET_VOLUME"
    SEARCH_GOOGLE = "SEARCH_GOOGLE"
    OPEN_APP_DYNAMIC = "OPEN_APP_DYNAMIC"
    SEARCH_MAP = "SEARCH_MAP"
    GET_TIME = "GET_TIME"
    CREATE_FOLDER = "CREATE_FOLDER"
    OPEN_BROWSER = "OPEN_BROWSER"
    OPEN_RECYCLE_BIN = "OPEN_RECYCLE_BIN"
    CLOSE_WINDOW = "CLOSE_WINDOW"
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    MUTE = "MUTE"
    BRIGHTNESS_UP = "BRIGHTNESS_UP"
    BRIGHTNESS_DOWN = "BRIGHTNESS_DOWN"
    MINIMIZE_WINDOW = "MINIMIZE_WINDOW"
    MAXIMIZE_WINDOW = "MAXIMIZE_WINDOW"
    OPEN_FOLDER = "OPEN_FOLDER"
    START_GESTURE = "START_GESTURE"
    UNKNOWN = "UNKNOWN"


@dataclass
class Intent:
    name: str
    parameters: Dict[str, str] = field(default_factory=dict)


def _normalize(text: str) -> str:
    normalized = " ".join(text.strip().lower().split())
    # Handle common spelling/pronunciation variants
    normalized = normalized.replace("thurakkuga", "thurakkuka")
    return normalized


PHRASE_MAP = {
    IntentName.CREATE_FOLDER: [
        "folder undakkuka",
        "puthiya folder",
        "pudhiya folder undakkuka",
        "create folder",
        "create a new folder",
        "make a new folder",
    ],
    IntentName.OPEN_BROWSER: [
        "browser thurakkuka",
        "browser thurakkuga",
        "chrome thurakkuka",
        "chrome thurakkuga",
        "browser open",
        "chrome open",
        "open browser",
        "open the browser",
        "open chrome",
    ], 
    IntentName.START_GESTURE: [
        "start gesture",
        "start the gesture",
        "start gesture control",
        "start gesture control",
    ],
    IntentName.OPEN_RECYCLE_BIN: [
        "recycle bin thurakkuka",
        "trash thurakkuka",
        "recycle bin open",
        "open recycle bin",
        "open the recycle bin",
        "open trash",
    ],
    IntentName.CLOSE_WINDOW: [
        "window adakkuka",
        "idhu adakkuka",
        "close window",
        "close this window",
        "close the app",
        "close this",
    ],
    IntentName.VOLUME_UP: [
        "shabdam kooduttuka",
        "volume kooduttuka",
        "volume up",
        "increase volume",
        "turn up the volume",
        "make it louder",
    ],
    IntentName.VOLUME_DOWN: [
        "shabdam kurakkuka",
        "volume kurakkuka",
        "volume down",
        "decrease volume",
        "turn down the volume",
        "make it quieter",
    ],
    IntentName.MUTE: [
        "mute cheyyu",
        "shabdam off",
        "volume mute",
        "mute the sound",
        "mute audio",
    ],
    IntentName.BRIGHTNESS_UP: [
        "brightness kooduttuka",
        "velicham kooduttuka",
        "brightness up",
        "increase brightness",
        "make it brighter",
        "turn up the brightness",
    ],
    IntentName.BRIGHTNESS_DOWN: [
        "brightness kurakkuka",
        "velicham kurakkuka",
        "brightness down",
        "decrease brightness",
        "make it dimmer",
        "turn down the brightness",
    ],
}


def parse_command(text: Optional[str]) -> Intent:
    if not text:
        return Intent(name=IntentName.UNKNOWN)

    normalized = _normalize(text)

    # -------------------------
    # 1. NUMERIC COMMANDS
    # -------------------------
    match = re.search(r'(\d{1,3})\s*%?\s*(brightness)', normalized)
    if match:
        value = int(match.group(1))
        return Intent(IntentName.SET_BRIGHTNESS, {"value": value})

    match = re.search(r'(\d{1,3})\s*%?\s*(volume)', normalized)
    if match:
        value = int(match.group(1))
        return Intent(IntentName.SET_VOLUME, {"value": value})

    # -------------------------
    # 2. GOOGLE SEARCH
    # -------------------------
    if normalized.startswith("google "):
        query = normalized.replace("google ", "")
        return Intent(IntentName.SEARCH_GOOGLE, {"query": query})

    # -------------------------
    # 3. MAP SEARCH
    # -------------------------
    if normalized.startswith("map ") or normalized.startswith("maps "):
        query = normalized.split(" ", 1)[1]
        return Intent(IntentName.SEARCH_MAP, {"query": query})

    # -------------------------
    # 4. OPEN APP (DYNAMIC)
    # -------------------------
    if normalized.startswith("open "):
        app = normalized.replace("open ", "")
        return Intent(IntentName.OPEN_APP_DYNAMIC, {"app": app})

    # -------------------------
    # 5. CREATE FOLDER
    # -------------------------
    if "create folder" in normalized:
        name = normalized.replace("create folder", "").strip()
        return Intent(IntentName.CREATE_FOLDER, {"folder_name": name})

    # -------------------------
    # 6. TIME / DATE
    # -------------------------
    if "time" in normalized or "date" in normalized:
        return Intent(IntentName.GET_TIME)

    if "gesture" in normalized:
        return Intent(IntentName.START_GESTURE)

    # -------------------------
    # 7. SIMPLE COMMANDS
    # -------------------------
    if "mute" in normalized:
        return Intent(IntentName.MUTE)

    if "volume up" in normalized:
        return Intent(IntentName.VOLUME_UP)

    if "volume down" in normalized:
        return Intent(IntentName.VOLUME_DOWN)

    if "brightness up" in normalized:
        return Intent(IntentName.BRIGHTNESS_UP)

    if "brightness down" in normalized:
        return Intent(IntentName.BRIGHTNESS_DOWN)

    if "close" in normalized:
        return Intent(IntentName.CLOSE_WINDOW)

    if "browser" in normalized:
        return Intent(IntentName.OPEN_BROWSER)

    if "trash" in normalized or "recycle bin" in normalized:
        return Intent(IntentName.OPEN_RECYCLE_BIN)
    
    if "minimize" in normalized:
        return Intent(IntentName.MINIMIZE_WINDOW)

    if "maximize" in normalized:
        return Intent(IntentName.MAXIMIZE_WINDOW)

    if "open folder" in normalized:
        name = normalized.replace("open folder", "").strip()
        return Intent(IntentName.OPEN_FOLDER, {"folder_name": name})

    return Intent(IntentName.UNKNOWN)

    
def _extract_folder_name(text: str, trigger_phrase: str) -> Optional[str]:
    """
    Very small heuristic to pull a folder name following the trigger phrase.
    """
    if trigger_phrase not in text:
        return None
    after = text.split(trigger_phrase, 1)[1].strip()
    return after or None

