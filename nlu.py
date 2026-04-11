from __future__ import annotations
from datetime import datetime
from datetime import datetime, timedelta
from config import get_settings
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Optional
import re
from logger import log


class IntentName:
    SET_BRIGHTNESS = "SET_BRIGHTNESS"
    SET_VOLUME = "SET_VOLUME"
    SEARCH_GOOGLE = "SEARCH_GOOGLE"
    OPEN_APP_DYNAMIC = "OPEN_APP_DYNAMIC"
    SEARCH_MAP = "SEARCH_MAP"
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
    GET_TIME = "GET_TIME"
    GET_DATE = "GET_DATE"
    GET_DAY = "GET_DAY"
    GET_DATE_DAY = "GET_DATE_DAY"
    GET_FULL_INFO = "GET_FULL_INFO"
    UNKNOWN = "UNKNOWN"
    EXIT = "EXIT"

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100
}

SYNONYMS = {
    "calculator": ["calc"],
    "vscode": ["code", "vs code"],
    "browser": ["chrome", "google chrome"]
}


def words_to_number(text):
    words = text.split()
    total = 0
    current = 0

    for word in words:
        if word in NUMBER_WORDS:
            val = NUMBER_WORDS[word]
            if val == 100:
                current *= val
            else:
                current += val
        else:
            if current > 0:
                total += current
                current = 0

    return total + current if (total + current) > 0 else None

@dataclass
class Intent:
    name: str
    parameters: Dict[str, str] = field(default_factory=dict)

def extract_app(normalized):
    APP_KEYWORDS = {
        "vscode": "vscode",
        "notepad": "notepad",
        "spotify": "spotify",
        "calculator": "calculator",
        "settings": "settings",
        "chrome": "chrome",
        "browser": "chrome",
        "telegram": "telegram",
        "whatsapp": "whatsapp"
    }

    for key in APP_KEYWORDS:
        if key in normalized:
            return APP_KEYWORDS[key]

    return None

def is_malayalam(text):
    return any('\u0D00' <= ch <= '\u0D7F' for ch in text)

def is_english(text: str) -> bool:
    return any(ch.isalpha() and ch.isascii() for ch in text)

def _normalize(text: str) -> str:
    normalized = " ".join(text.strip().lower().split())
    # Handle common spelling/pronunciation variants
    normalized = normalized.replace("thurakkuga", "thurakkuka")
    normalized = normalized.replace("kurakku", "down")
    normalized = normalized.replace("kootu", "up")
    normalized = normalized.replace("koottu", "up")
    normalized = normalized.replace("koottu", "kootu")
    normalized = normalized.replace("kurakku", "kurakkan")
    normalized = normalized.replace("kurakkan", "down")
    normalized = normalized.replace("kurakku", "down")
    normalized = normalized.replace("kurakkan", "down")

    normalized = normalized.replace("thurakku", "open")
    normalized = normalized.replace("cheyyu", "")
    normalized = normalized.replace("cyu", "")
    normalized = normalized.replace("percentage", "")
    normalized = normalized.replace("like", "")
    normalized = normalized.replace("around", "")
    normalized = normalized.replace("approximately", "")
    normalized = normalized.replace("percent", "")
    normalized = normalized.replace("cat gesture", "start gesture")
    normalized = normalized.replace("chat gesture", "start gesture")
    normalized = normalized.replace("%", "")
    normalized = normalized.replace("maappu", "map")
    normalized = normalized.replace("maap", "map")

    normalized = re.sub(r'\b(to|the|a|uh|um|like|bro|yo|hey|my|please|can|you|me)\b', '', normalized)
    normalized = " ".join(normalized.split())
    normalized = normalized.replace("can you", "")
    normalized = normalized.replace("please", "")

    if "calc" in normalized:
        normalized = normalized.replace("calc", "calculator")

    # FIX VS CODE NORMALIZATION (NO CASCADE)
    normalized = normalized.replace("vs code", "vscode")

    # ONLY replace standalone "code"
    normalized = re.sub(r'\bcode\b', 'vscode', normalized)
    if "kurakku" in normalized:
        normalized = normalized.replace("kurakku", "down")

    for key, variants in SYNONYMS.items():
        for v in variants:
            if v in normalized:
                normalized = normalized.replace(v, key)

    return normalized

def clean_text(text):
    return text.lower().strip()


def normalize_text(text: str) -> str:
    text = text.lower().strip()

    # Remove filler words
    fillers = ["please", "can you", "could you", "tell me", "hey", "gestvoice"]
    for f in fillers:
        text = text.replace(f, "")

    # Normalize spacing
    text = " ".join(text.split())

    return text


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

MALAYALAM_MAP = {
    "തിരയൂ": "search",
    "ഗൂഗിളിൽ": "google",
    "വോള്യം": "volume",
    "ശബ്ദം": "volume",
    "കുറയ്ക്കൂ": "down",
    "കാൽക്കുലേറ്റർ": "calculator",
    "നോട്ട്‌പാഡ്": "notepad",
    "മാപ്പ്": "map",
    "ലൊക്കേഷൻ": "location",
    "സ്ഥലം": "location",
    "തുറക്കൂ": "open"
}

def map_malayalam(text):
    for k, v in MALAYALAM_MAP.items():
        text = text.replace(k, v)
    return text


def is_valid_command(text):
    return bool(text and len(text.strip()) > 1)

def parse_command(text: Optional[str]) -> Intent:
    if not text:
        return Intent(IntentName.UNKNOWN)

    if not is_valid_command(text):
        return Intent(IntentName.UNKNOWN)

    # -------------------------
    # 🔥 MALAYALAM DIRECT MAP
    # -------------------------
    if is_malayalam(text):
        if "ക്രോം" in text or "ബ്രൗസർ" in text:
            return Intent(IntentName.OPEN_BROWSER)

        if "സമയം" in text:
            return Intent(IntentName.GET_TIME)

        if "ഫോൾഡർ" in text:
            return Intent(IntentName.CREATE_FOLDER)

    # 🔥 Normalize
    text = normalize_text(text)
    text = map_malayalam(text)
    normalized = _normalize(text)
    

    log(f"Normalized command: {normalized}")

    # -------------------------
    # 🔥 MAP SEARCH (HIGH PRIORITY) — FIXED
    # -------------------------
    if any(word in normalized for word in ["map", "maps", "location", "navigate", "direction"]):
        words = normalized.split()

        REMOVE_WORDS = {"map", "maps", "location", "navigate", "direction"}

        filtered_words = [w for w in words if w not in REMOVE_WORDS]

        query = " ".join(filtered_words).strip()

        if not query:
            query = "current location"

        return Intent(IntentName.SEARCH_MAP, {"query": query})

    # -------------------------
    # 🔥 SEARCH (HIGH PRIORITY) — FIXED
    # -------------------------
    if any(word in normalized for word in ["search", "google", "find", "lookup", "look up"]):
        words = normalized.split()

        REMOVE_WORDS = {
            "search", "google", "find", "lookup", "look", "up",
            "googleil", "il", "thirayoo", "thirayuka"
        }

        filtered_words = [w for w in words if w not in REMOVE_WORDS]

        query = " ".join(filtered_words).strip()

        if not query:
            query = "google"

        return Intent(IntentName.SEARCH_GOOGLE, {"query": query})

    # -------------------------
    # 🔥 CREATE FOLDER (SMART)
    # -------------------------
    if "folder" in normalized:
        name = normalized.replace("create", "").replace("make", "").replace("folder", "").strip()
        return Intent(IntentName.CREATE_FOLDER, {"name": name or "new_folder"})


    # -------------------------
    # ✅ NUMBER COMMANDS (FIXED)
    # -------------------------

    # Clean noise words
    normalized = normalized.replace("around", "")
    normalized = normalized.replace("maybe", "")
    normalized = normalized.replace("approximately", "")
    # 1. sound → volume
    normalized = normalized.replace("sound", "volume")

    # 2. kurakku variants
    normalized = normalized.replace("kurakku", "down")
    normalized = normalized.replace("kurakkan", "down")

    # 3. strong noise removal
    normalized = re.sub(
        r'\b(uh|um|like|bro|yo|hey|please|can you|could you|would you|tell me)\b',
        '',
        normalized
    )

    # 🔥 STEP 1: Extract number (DIGIT or WORD)
    num = None

    # Try digit
    digit_match = re.search(r'(\d{1,3})', normalized)
    if digit_match:
        num = int(digit_match.group(1))

    # Try word number
    if num is None:
        num = words_to_number(normalized)

    # 🔥 STEP 2: HANDLE VOLUME
    if "volume" in normalized:
        if num is not None:
            return Intent(IntentName.SET_VOLUME, {"value": num})

        if "up" in normalized or "increase" in normalized:
            return Intent(IntentName.VOLUME_UP)

        if "down" in normalized or "decrease" in normalized:
            return Intent(IntentName.VOLUME_DOWN)

    # 🔥 STEP 3: HANDLE BRIGHTNESS
    if "brightness" in normalized:
        if num is not None:
            return Intent(IntentName.SET_BRIGHTNESS, {"value": num})

        if "up" in normalized or "increase" in normalized:
            return Intent(IntentName.BRIGHTNESS_UP)

        if "down" in normalized or "decrease" in normalized:
            return Intent(IntentName.BRIGHTNESS_DOWN)

    # -------------------------
    #  WEATHER 
    # -------------------------


    if "weather" in normalized:
        return Intent(IntentName.UNKNOWN)

    # -------------------------
    # ✅ DATE / TIME / DAY
    # -------------------------
    if "naale" in normalized:
        return Intent("GET_TOMORROW")

    if "mattannaal" in normalized:
        return Intent("GET_DAY_AFTER_TOMORROW")

    if "yesterday" in normalized or "innale" in normalized:
        return Intent("GET_YESTERDAY")

    if "time" in normalized or "samayam" in normalized:
        return Intent(IntentName.GET_TIME)

    if "thiyathi" in normalized or "date" in normalized:
        return Intent(IntentName.GET_DATE)

    if "divasam" in normalized or "day" in normalized:
        return Intent(IntentName.GET_DAY)

    # -------------------------
    # ✅  SIMPLE COMMANDS
    # -------------------------

    
    if "mute" in normalized:
        return Intent(IntentName.MUTE)

    if "volume" in normalized:
        if "up" in normalized or "increase" in normalized or "kootu" in normalized or "koottu" in normalized:
            return Intent(IntentName.VOLUME_UP)

        if "down" in normalized or "decrease" in normalized or "kurakkan" in normalized:
            return Intent(IntentName.VOLUME_DOWN)
        
    if "brightness" in normalized:
        if "up" in normalized or "increase" in normalized or "kootu" in normalized or "koottu" in normalized:
            return Intent(IntentName.BRIGHTNESS_UP)

        if "down" in normalized or "decrease" in normalized  or "kurakkan" in normalized:
            return Intent(IntentName.BRIGHTNESS_DOWN)

    if "close" in normalized:
        return Intent(IntentName.CLOSE_WINDOW)

    if "gesture" in normalized:
        return Intent(IntentName.START_GESTURE)

    if "exit" in normalized:
        return Intent(IntentName.EXIT)

    if "trash" in normalized or "recycle bin" in normalized:
        return Intent(IntentName.OPEN_RECYCLE_BIN)

    if "minimize" in normalized:
        return Intent(IntentName.MINIMIZE_WINDOW)

    if "maximize" in normalized:
        return Intent(IntentName.MAXIMIZE_WINDOW)

    if "open folder" in normalized:
        name = normalized.replace("open folder", "").strip()
        return Intent(IntentName.OPEN_FOLDER, {"folder_name": name})


    # -------------------------
    # ✅ STRONG PHRASE MATCH (PRIMARY)
    # -------------------------
    for intent_name, phrases in PHRASE_MAP.items():
        for phrase in phrases:
            if phrase in normalized:
                return Intent(intent_name)


    # -------------------------
    # ✅ OPEN APP (SMART)
    # -------------------------
    if "open" in normalized:
        app = extract_app(normalized)

        if app:
            return Intent(IntentName.OPEN_APP_DYNAMIC, {"app": app})
        
        return Intent(IntentName.UNKNOWN)

    if "open" in normalized:
        words = [w for w in normalized.split() if w not in ["open", "please", "app", "the", "my"]]
        
        if not words:
            return Intent(IntentName.OPEN_APP_DYNAMIC, {"app": "chrome"})
        
        return Intent(IntentName.OPEN_APP_DYNAMIC, {"app": " ".join(words)})

    # -------------------------
    # 💬 SMALL TALK HANDLING
    # -------------------------
    if any(word in normalized for word in ["sukham", "sukhamano", "vishesham", "hello", "hi"]):
        return Intent("SMALL_TALK")

    # -------------------------
    # ❌ UNKNOWN
    # -------------------------
    log(f"Unknown command: {normalized}")
    return Intent(IntentName.UNKNOWN)

def fallback_response(text):
    if "time" in text:
        return "Did you mean to ask the time?"
    elif "open" in text:
        return "Which application should I open?"
    else:
        return "I didn't understand. Try saying something like 'open chrome' or 'what is the time'"

def _extract_folder_name(text: str, trigger_phrase: str) -> Optional[str]:
    """
    Very small heuristic to pull a folder name following the trigger phrase.
    """
    if trigger_phrase not in text:
        return None
    after = text.split(trigger_phrase, 1)[1].strip()
    return after or None

