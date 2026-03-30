from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# --- MuRIL optional semantic support ---
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    _MURIL_AVAILABLE = True
except Exception:
    _MURIL_AVAILABLE = False

_MURIL_MODEL_NAME = "google/muril-base-cased"
_muril_tokenizer = None
_muril_model = None
_muril_intent_bank = None

class IntentName:
    CREATE_FOLDER = "CREATE_FOLDER"
    OPEN_BROWSER = "OPEN_BROWSER"
    OPEN_RECYCLE_BIN = "OPEN_RECYCLE_BIN"
    CLOSE_WINDOW = "CLOSE_WINDOW"
    MINIMIZE_WINDOW = "MINIMIZE_WINDOW"
    MAXIMIZE_WINDOW = "MAXIMIZE_WINDOW"
    SWITCH_WINDOW = "SWITCH_WINDOW"
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    MUTE = "MUTE"
    BRIGHTNESS_UP = "BRIGHTNESS_UP"
    BRIGHTNESS_DOWN = "BRIGHTNESS_DOWN"
    OPEN_YOUTUBE = "OPEN_YOUTUBE"
    OPEN_NOTEPAD = "OPEN_NOTEPAD"
    OPEN_CALCULATOR = "OPEN_CALCULATOR"
    EMPTY_RECYCLE_BIN = "EMPTY_RECYCLE_BIN"
    OPEN_PATH_DYNAMIC = "OPEN_PATH_DYNAMIC"
    CLOSE_ACTIVE_ITEM = "CLOSE_ACTIVE_ITEM"
    TELL_TIME = "TELL_TIME"
    TELL_DATE = "TELL_DATE"
    TELL_DAY = "TELL_DAY"
    OPEN_MAP = "OPEN_MAP"
    SEARCH_WEB = "SEARCH_WEB"
    SET_VOLUME = "SET_VOLUME"
    SET_BRIGHTNESS = "SET_BRIGHTNESS"
    UNKNOWN = "UNKNOWN"



@dataclass
class Intent:
    name: str
    parameters: Dict[str, str] = field(default_factory=dict)


def _normalize(text: str) -> str:
    normalized = " ".join(text.strip().lower().split())
    # Handle common spelling/pronunciation variants
    normalized = normalized.replace("thurakkuga", "thurakkuka")

    # Remove filler words (helps MuRIL + rules)
    fillers = ["can you", "please", "could you", "would you"]
    for f in fillers:
        normalized = normalized.replace(f, "")
    return normalized.strip()

# ---------------------------
# MuRIL FUNCTIONS
# ---------------------------

def _load_muril():
    global _muril_tokenizer, _muril_model, _muril_intent_bank

    if not _MURIL_AVAILABLE:
        return None, None, None

    if _muril_tokenizer is None:
        _muril_tokenizer = AutoTokenizer.from_pretrained(_MURIL_MODEL_NAME)
        _muril_model = AutoModel.from_pretrained(_MURIL_MODEL_NAME)
        _muril_model.eval()

    if _muril_intent_bank is None:
        examples = {
            IntentName.BRIGHTNESS_UP: [
                "increase brightness",
                "make screen brighter",
                "make it brighter",
            ],
            IntentName.BRIGHTNESS_DOWN: [
                "decrease brightness",
                "reduce brightness",
                "make it dim",
            ],
            IntentName.VOLUME_UP: [
                "increase volume",
                "make it louder",
                "turn volume up",
            ],
            IntentName.VOLUME_DOWN: [
                "decrease volume",
                "make it quieter",
                "turn volume down",
            ],
            IntentName.OPEN_BROWSER: [
                "open browser",
                "launch chrome",
                "start browser",
            ],
        }

        bank = []
        for intent, phrases in examples.items():
            for text in phrases:
                emb = _muril_embed(text)
                bank.append((intent, emb))
        _muril_intent_bank = bank

    return _muril_tokenizer, _muril_model, _muril_intent_bank


def _muril_embed(text: str):
    tokenizer = _muril_tokenizer
    model = _muril_model

    encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=64)
    with torch.no_grad():
        out = model(**encoded)

    last_hidden = out.last_hidden_state
    mask = encoded["attention_mask"].unsqueeze(-1)
    summed = (last_hidden * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    emb = summed / counts
    return emb[0]


def _muril_semantic_match(text: str) -> Optional[Intent]:
    tokenizer, model, bank = _load_muril()
    if not tokenizer:
        return None

    query = _muril_embed(text)

    best_intent = None
    best_score = -1

    for intent_name, emb in bank:
        score = torch.nn.functional.cosine_similarity(
            query.unsqueeze(0), emb.unsqueeze(0)
        ).item()

        if score > best_score:
            best_score = score
            best_intent = intent_name

    # Threshold (tune if needed)
    # Higher threshold reduces random intent picks from noisy/incorrect transcripts.
    if best_score > 0.88:
        return Intent(name=best_intent)

    return None


def _contains_semantic_match_signals(normalized_text: str) -> bool:
    """
    Muril semantic matching should only run when we're likely dealing with
    the intents Muril knows about (volume/brightness/open browser).

    This prevents false positives like repeatedly triggering volume-up
    from unrelated speech/noise.
    """
    signals = [
        # Volume / sound
        "volume",
        "shabdam",   # transliteration for Malayalam "sound/volume"
        "ശബ്ദം",
        "വോള്യം",
        # Brightness / light
        "brightness",
        "velicham",  # transliteration for Malayalam "brightness/light"
        "പ്രകാശം",
        "ബ്രൈറ്റ്‌നസ്",
        # Browser
        "browser",
        "chrome",
        "ബ്രൗസർ",
        "ക്രോം",
    ]
    return any(s in normalized_text for s in signals)

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
    IntentName.MINIMIZE_WINDOW: [
        "minimize window",
        "minimise window",
        "window minimize cheyyu",
        "window kurakkuka",
    ],
    IntentName.MAXIMIZE_WINDOW: [
        "maximize window",
        "maximise window",
        "window maximize cheyyu",
        "window valuthakkuka",
    ],
    IntentName.SWITCH_WINDOW: [
        "switch window",
        "next window",
        "window maattuka",
        "change window",
    ],
    IntentName.VOLUME_UP: [
        "shabdam kooduttuka",
        "volume kooduttuka",
        "volume up",
        "increase volume",
        "turn up the volume",
        "volume up",
        "make it louder",
    ],
    IntentName.VOLUME_DOWN: [
        "shabdam kurakkuka",
        "volume kurakkuka",
        "volume down",
        "decrease volume",
        "reduce volume",
        "volume down",
        "turn down the volume",
        "make it quieter",
    ],
    IntentName.MUTE: [
        "mute cheyyu",
        "shabdum off",
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
    IntentName.OPEN_YOUTUBE: [
        "open youtube",
        "youtube thurakkuka",
        "youtube open",
    ],
    IntentName.OPEN_NOTEPAD: [
        "open notepad",
        "notepad thurakkuka",
        "notepad open",
    ],
    IntentName.OPEN_CALCULATOR: [
        "open calculator",
        "calculator thurakkuka",
        "calculator open",
    ],
    IntentName.EMPTY_RECYCLE_BIN: [
        "empty recycle bin",
        "clear recycle bin",
        "recycle bin clear cheyyu",
        "recycle bin empty cheyyu",
    ],
    IntentName.CLOSE_ACTIVE_ITEM: [
        "close this",
        "close file",
        "close folder",
        "file adakkuka",
        "folder adakkuka",
    ],
    IntentName.TELL_TIME: [
        "what is the time",
        "current time",
        "samayam entha",
        "time parayu",
        "time",
    ],
    IntentName.TELL_DATE: [
        "what is the date",
        "today's date",
        "date parayu",
        "inni entha thethi",
        "date",
    ],
    IntentName.TELL_DAY: [
        "what day is today",
        "which day is today",
        "what day is it",
        "today which day",
        "inni entha divasam",
        "day parayu",
        "day",
    ],
    IntentName.OPEN_MAP: [
        "open map",
        "open maps",
        "google maps thurakkuka",
        "map thurakkuka",
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

    # Dynamic web search: "search <something>" or "google <something>"
    search_query: Optional[str] = None
    if normalized.startswith("search "):
        search_query = normalized[len("search ") :].strip()
    elif normalized.startswith("google "):
        search_query = normalized[len("google ") :].strip()
    elif normalized.startswith("google search "):
        search_query = normalized[len("google search ") :].strip()

    if search_query:
        return Intent(name=IntentName.SEARCH_WEB, parameters={"query": search_query})

    # Explicit "open folder X", "open file X", "open app X" (and Malayalam-style)
    if normalized.startswith("open folder "):
        target = normalized[len("open folder ") :].strip()
        if target:
            return Intent(name=IntentName.OPEN_PATH_DYNAMIC, parameters={"target": target, "kind": "folder"})
    if normalized.startswith("open file "):
        target = normalized[len("open file ") :].strip()
        if target:
            return Intent(name=IntentName.OPEN_PATH_DYNAMIC, parameters={"target": target, "kind": "file"})
    if normalized.startswith("open app "):
        target = normalized[len("open app ") :].strip()
        if target:
            return Intent(name=IntentName.OPEN_PATH_DYNAMIC, parameters={"target": target, "kind": "app"})
    if normalized.startswith("folder ") and normalized.endswith(" thurakkuka"):
        target = normalized[len("folder ") : -len(" thurakkuka")].strip()
        if target:
            return Intent(name=IntentName.OPEN_PATH_DYNAMIC, parameters={"target": target, "kind": "folder"})
    if normalized.startswith("file ") and normalized.endswith(" thurakkuka"):
        target = normalized[len("file ") : -len(" thurakkuka")].strip()
        if target:
            return Intent(name=IntentName.OPEN_PATH_DYNAMIC, parameters={"target": target, "kind": "file"})
    if normalized.startswith("app ") and normalized.endswith(" thurakkuka"):
        target = normalized[len("app ") : -len(" thurakkuka")].strip()
        if target:
            return Intent(name=IntentName.OPEN_PATH_DYNAMIC, parameters={"target": target, "kind": "app"})

    # Generic open: "open X" or "X thurakkuka" (try folder, then app, then file)
    target = None
    if normalized.startswith("open "):
        target = normalized[len("open ") :].strip()
    elif normalized.endswith(" thurakkuka"):
        target = normalized[: -len(" thurakkuka")].strip()

    if target:
        return Intent(name=IntentName.OPEN_PATH_DYNAMIC, parameters={"target": target})
    
    # --- Absolute volume control ---
    vol_match = re.search(r"(?:set )?volume(?: to)? (\d{1,3})", normalized)
    if vol_match:
        value = int(vol_match.group(1))
        value = max(0, min(100, value))
        return Intent(name=IntentName.SET_VOLUME,parameters={"level": str(value)})

    # --- Absolute brightness control ---
    bright_match = re.search(r"(?:set )?(?:screen )?brightness(?: to)? (\d{1,3})", normalized)
    if bright_match:
        value = int(bright_match.group(1))
        value = max(0, min(100, value))
        return Intent(name=IntentName.SET_BRIGHTNESS,parameters={"level": str(value)})

    # Contextual overrides
    if "too loud" in normalized or "very loud" in normalized:
        return Intent(IntentName.VOLUME_DOWN)

    if "too dark" in normalized:
        return Intent(IntentName.BRIGHTNESS_UP)

    if "too bright" in normalized:
        return Intent(IntentName.BRIGHTNESS_DOWN)
    
    if _contains_semantic_match_signals(normalized):
        muril_intent = _muril_semantic_match(normalized)
        if muril_intent:
            return muril_intent
    
    return Intent(name=IntentName.UNKNOWN)


def _extract_folder_name(text: str, trigger_phrase: str) -> Optional[str]:
    """
    Very small heuristic to pull a folder name following the trigger phrase.
    """
    if trigger_phrase not in text:
        return None
    after = text.split(trigger_phrase, 1)[1].strip()
    return after or None
 
