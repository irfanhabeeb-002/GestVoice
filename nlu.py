from __future__ import annotations
from datetime import datetime
from datetime import datetime, timedelta
from config import get_settings
from dataclasses import dataclass, field
from difflib import SequenceMatcher
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()
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


@dataclass
class Intent:
    name: str
    parameters: Dict[str, str] = field(default_factory=dict)

def is_malayalam(text: str) -> bool:
    # Malayalam Unicode range
    return any('\u0D00' <= ch <= '\u0D7F' for ch in text)

def is_english(text: str) -> bool:
    return any(ch.isalpha() and ch.isascii() for ch in text)

def _normalize(text: str) -> str:
    normalized = " ".join(text.strip().lower().split())
    # Handle common spelling/pronunciation variants
    normalized = normalized.replace("thurakkuga", "thurakkuka")
    return normalized

def clean_text(text):
    return text.lower().strip()

def normalize_script(text):
    import unicodedata

    cleaned = ""

    for ch in text:
        try:
            name = unicodedata.name(ch)
            if "DEVANAGARI" in name:
                continue  # REMOVE Hindi chars
            else:
                cleaned += ch
        except:
            cleaned += ch

    return cleaned

def normalize_semantics(text):
    replacements = {
        # brightness variations
        "lightness": "brightness",
        "bright": "brightness",
        "brite": "brightness",

        # kootu variations
        "coot": "kootu",
        "coot too": "kootu",
        "couture": "kootu",

        # kurakku variations
        "kurakoo": "kurakkan",
        "kurakoo": "kurakkan",
        "kurakku": "kurakkan",

        # thurakku variations
        "tora": "thurakku",
        "kodar": "thurakku",
        "turak": "thurakku",
    }

    for wrong, correct in replacements.items():
        if wrong in text:
            text = text.replace(wrong, correct)

    return text

def normalize_phonetics(text):
    replacements = {
        # Chrome variations
        "krom": "chrome",
        "grom": "chrome",
        "chrom": "chrome",

        # Thura variations
        "turaku": "thurakku",
        "turak": "thurakku",
        "turaka": "thurakku",
        "turakk": "thurakku",
        "turakkar": "thurakku",
        "turakugam": "thurakku",
        "tura": "thurakku",

        # Volume variations
        "volium": "volume",
        "bolium": "volume",
        "ulyam": "volume",
        "bulyam": "volume",

        # Kurakkan variations
        "korakkan": "kurakkan",
        "kurakan": "kurakkan",
        "kurakuga": "kurakkan",
        "kurkkan": "kurakkan",
    }

    for wrong, correct in replacements.items():
        if wrong in text:
            text = text.replace(wrong, correct)

    return text


COMMAND_KEYWORDS = {
    "open": ["open", "thurakku"],
    "chrome": ["chrome", "browser"],

    "volume": ["volume"],
    "down": ["down", "kurakkan"],
    "up": ["up", "kootu", "koottu"],

    "brightness": ["brightness", "lightness", "bright"],
}


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
    "time": ["samayam", "entha samayam", "time entha"],
    "date": ["divasam", "entha divasam", "date entha"],
    "open": ["thurakku", "thurakkuka", "thura"],
    "close": ["adakku", "adakkuka"],
    "volume up": ["shabdam kootu", "volume kootu", "koottu"],
    "volume down": ["shabdam kurakkan", "volume kurakkan", "kurakkan"],
    "brightness up": ["velicham kootu"],
    "brightness down": ["velicham kurakkan"],
}

def match_word(word, choices):
    best = None
    best_score = 0

    for c in choices:
        score = similarity(word, c)
        if score > best_score:
            best_score = score
            best = c

    if best_score > 0.6:
        return best
    return None

def extract_intent_tokens(text):
    words = text.split()
    matched = []

    for w in words:
        for key, variants in COMMAND_KEYWORDS.items():
            if match_word(w, variants):
                matched.append(key)

    return matched

def detect_intent_from_tokens(tokens):
    if "open" in tokens and "chrome" in tokens:
        return Intent(IntentName.OPEN_APP_DYNAMIC, {"app": "chrome"})

    if "volume" in tokens and "down" in tokens:
        return Intent(IntentName.VOLUME_DOWN)

    if "volume" in tokens and "up" in tokens:
        return Intent(IntentName.VOLUME_UP)
    
    if "brightness" in tokens and "up" in tokens:
        return Intent(IntentName.BRIGHTNESS_UP)

    if "brightness" in tokens and "down" in tokens:
        return Intent(IntentName.BRIGHTNESS_DOWN)

    if "time" in tokens:
        return Intent(IntentName.GET_TIME)

    return Intent(IntentName.UNKNOWN)



def map_malayalam(text):
    for key, variants in MALAYALAM_MAP.items():
        for v in variants:
            if v in text:
                text = text.replace(v, key)
    return text

def is_valid_command(text):
    if len(text) < 3:
        return False

    garbage_words = ["uh", "hmm", "noise"]
    if any(g in text for g in garbage_words):
        return False

    return True



def process_text(text):
    text = clean_text(text)
    text = normalize_script(text)
    text = normalize_phonetics(text)

    # 🔥 NEW STEP
    text = normalize_semantics(text)
    tokens = extract_intent_tokens(text)

    return detect_intent_from_tokens(tokens)



def parse_command(text: Optional[str]) -> Intent:
    if not text:
        return Intent(name=IntentName.UNKNOWN)

    # STEP 1: Basic validation
    if not is_valid_command(text):
        return Intent(IntentName.UNKNOWN)

    # STEP 2: Normalize text
    text = normalize_text(text)

    # STEP 3: Malayalam mapping
    text = map_malayalam(text)

    # STEP 4: Final normalization
    normalized = _normalize(text)
    log(f"Normalized command: {normalized}")

    # 🔥 FIRST: fuzzy handling
    fuzzy_intent = process_text(normalized)
    if fuzzy_intent.name != IntentName.UNKNOWN:
        log(f"Fuzzy intent detected: {fuzzy_intent}")
        return fuzzy_intent

# THEN: regex + rules
    # -------------------------
    #  SET VOLUME / BRIGHTNESS (STRONG MATCH)
    # -------------------------

    # Volume (set to X)
    match = re.search(r'(?:set|change)?\s*volume\s*(?:to)?\s*(\d{1,3})', normalized)
    if match:
        value = int(match.group(1))
        return Intent(IntentName.SET_VOLUME, {"value": value})

    # Brightness (set to X)
    match = re.search(r'(?:set|change)?\s*brightness\s*(?:to)?\s*(\d{1,3})', normalized)
    if match:
        value = int(match.group(1))
        return Intent(IntentName.SET_BRIGHTNESS, {"value": value})

    # -------------------------
    #  GOOGLE SEARCH
    # -------------------------
    if normalized.startswith("google "):
        query = normalized.replace("google ", "")
        return Intent(IntentName.SEARCH_GOOGLE, {"query": query})

    # -------------------------
    #  MAP SEARCH
    # -------------------------
    if normalized.startswith("map ") or normalized.startswith("maps "):
        query = normalized.split(" ", 1)[1]
        return Intent(IntentName.SEARCH_MAP, {"query": query})


    #  CREATE FOLDER
    # -------------------------
    if "create folder" in normalized:
        name = normalized.replace("create folder", "").strip()
        return Intent(IntentName.CREATE_FOLDER, {"folder_name": name})

    # -------------------------
    #  TIME / DATE
    # -------------------------
    
    if "yesterday" in normalized:
        return Intent("GET_YESTERDAY")
    
    if "day after tomorrow" in normalized:
        return Intent("GET_DAY_AFTER_TOMORROW")

    if "tomorrow" in normalized:
        return Intent("GET_TOMORROW")

    TIME_KEYWORDS = ["time", "current time", "what time"]
    DATE_KEYWORDS = ["date", "today date"]
    DAY_KEYWORDS = ["day", "today"]

    if any(k in normalized for k in TIME_KEYWORDS):
        if any(k in normalized for k in DATE_KEYWORDS + DAY_KEYWORDS):
            return Intent(IntentName.GET_FULL_INFO)
        return Intent(IntentName.GET_TIME)

    if any(k in normalized for k in DATE_KEYWORDS):
        if any(k in normalized for k in DAY_KEYWORDS):
            return Intent(IntentName.GET_DATE_DAY)
        return Intent(IntentName.GET_DATE)

    if any(k in normalized for k in DAY_KEYWORDS):
        return Intent(IntentName.GET_DAY)

    if "date" in normalized:
        if "day" in normalized:
            return Intent("GET_DATE_DAY")
        return Intent("GET_DATE")

    if "today" in normalized:
        return Intent("GET_DATE_DAY")  

    if "day" in normalized:
        return Intent("GET_DAY")

    if "gesture" in normalized:
        return Intent(IntentName.START_GESTURE)

    if "exit" in normalized:
        return Intent("EXIT")

    # -------------------------
    #  SIMPLE COMMANDS
    # -------------------------
    if "mute" in normalized:
        return Intent(IntentName.MUTE)

    if "increase volume" in normalized:
        return Intent(IntentName.VOLUME_UP)

    if "decrease volume" in normalized:
        return Intent(IntentName.VOLUME_DOWN)

    if "increase brightness" in normalized:
        return Intent(IntentName.BRIGHTNESS_UP)

    if "decrease brightness" in normalized:
        return Intent(IntentName.BRIGHTNESS_DOWN)       

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

    if "recycle bin" in normalized or "trash" in normalized:
        return Intent(IntentName.OPEN_RECYCLE_BIN)
    
    if normalized.startswith("open "):
        app = normalized.replace("open ", "").split(".")[0].strip()
        return Intent(IntentName.OPEN_APP_DYNAMIC, {"app": app})


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

