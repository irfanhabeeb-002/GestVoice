from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class IntentName:
    CREATE_FOLDER = "CREATE_FOLDER"
    OPEN_BROWSER = "OPEN_BROWSER"
    OPEN_RECYCLE_BIN = "OPEN_RECYCLE_BIN"
    CLOSE_WINDOW = "CLOSE_WINDOW"
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    MUTE = "MUTE"
    BRIGHTNESS_UP = "BRIGHTNESS_UP"
    BRIGHTNESS_DOWN = "BRIGHTNESS_DOWN"
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

    for intent_name, phrases in PHRASE_MAP.items():
        for phrase in phrases:
            if phrase in normalized:
                if intent_name == IntentName.CREATE_FOLDER:
                    folder_name = _extract_folder_name(normalized, phrase)
                    params = {"folder_name": folder_name} if folder_name else {}
                    return Intent(name=intent_name, parameters=params)
                return Intent(name=intent_name)

    return Intent(name=IntentName.UNKNOWN)


def _extract_folder_name(text: str, trigger_phrase: str) -> Optional[str]:
    """
    Very small heuristic to pull a folder name following the trigger phrase.
    """
    if trigger_phrase not in text:
        return None
    after = text.split(trigger_phrase, 1)[1].strip()
    return after or None

