from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
import datetime
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
from config import get_settings
from nlu import Intent, IntentName
from logger import log

@dataclass
class ActionResult:
    success: bool
    user_message: str


def _ensure_base_folder() -> str:
    settings = get_settings()
    os.makedirs(settings.base_folder_path, exist_ok=True)
    return settings.base_folder_path


def create_folder(intent: Intent) -> ActionResult:
    base_path = _ensure_base_folder()
    folder_name = intent.parameters.get("folder_name")
    if not folder_name:
        folder_name = time.strftime("Folder_%Y%m%d_%H%M%S")

    safe_name = "".join(c for c in folder_name if c not in r'<>:"/\\|?*')
    path = os.path.join(base_path, safe_name or "NewFolder")
    os.makedirs(path, exist_ok=True)

    try:
        # macOS: open the folder in Finder
        subprocess.Popen(["open", path])
    except Exception:
        pass

    return ActionResult(True, f"Folder created at {path}")


def open_browser(_: Intent) -> ActionResult:
    settings = get_settings()
    try:
        # macOS: 'open' handles URLs and opens the default browser
        subprocess.Popen(["open", settings.homepage_url])
    except Exception as exc:
        return ActionResult(False, f"Failed to open browser: {exc}")
    return ActionResult(True, "Browser opened.")


def open_recycle_bin(_: Intent) -> ActionResult:
    try:
        # macOS: open the Trash folder in Finder
        trash_path = os.path.expanduser("~/.Trash")
        subprocess.Popen(["open", trash_path])
    except Exception as exc:
        return ActionResult(False, f"Failed to open Trash: {exc}")
    return ActionResult(True, "Trash opened.")


def close_window(_: Intent) -> ActionResult:
    try:
        # macOS: send Cmd+W via osascript
        subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to keystroke "w" using command down'],
            check=True,
        )
    except Exception as exc:
        return ActionResult(False, f"Failed to close window: {exc}")
    return ActionResult(True, "Active window closed.")


def volume_up(_: Intent) -> ActionResult:
    try:
        # macOS: use osascript to increase volume by 10
        subprocess.run(
            ["osascript", "-e",
             "set curVol to output volume of (get volume settings)\n"
             "set volume output volume (curVol + 10)"],
            check=True,
        )
    except Exception as exc:
        return ActionResult(False, f"Failed to increase volume: {exc}")
    return ActionResult(True, "Volume increased.")


def volume_down(_: Intent) -> ActionResult:
    try:
        # macOS: use osascript to decrease volume by 10
        subprocess.run(
            ["osascript", "-e",
             "set curVol to output volume of (get volume settings)\n"
             "set volume output volume (curVol - 10)"],
            check=True,
        )
    except Exception as exc:
        return ActionResult(False, f"Failed to decrease volume: {exc}")
    return ActionResult(True, "Volume decreased.")


def volume_mute(_: Intent) -> ActionResult:
    try:
        # macOS: toggle mute via osascript
        subprocess.run(
            ["osascript", "-e",
             "set muteState to output muted of (get volume settings)\n"
             "set volume output muted (not muteState)"],
            check=True,
        )
    except Exception as exc:
        return ActionResult(False, f"Failed to mute/unmute volume: {exc}")
    return ActionResult(True, "Volume muted or unmuted.")


def brightness_up(_: Intent) -> ActionResult:
    try:
        subprocess.run([
            "osascript",
            "-e",
            'tell application "System Events" to key code 144'
        ], check=True)
    except Exception as exc:
        return ActionResult(False, f"Failed to increase brightness: {exc}")
    return ActionResult(True, "Brightness increased.")


def brightness_down(_: Intent) -> ActionResult:
    try:
        subprocess.run([
            "osascript",
            "-e",
            'tell application "System Events" to key code 145'
        ], check=True)
    except Exception as exc:
        return ActionResult(False, f"Failed to decrease brightness: {exc}")
    return ActionResult(True, "Brightness decreased.")

def set_brightness(intent: Intent) -> ActionResult:
    value = int(intent.parameters.get("value", 50))

    try:
        subprocess.run([
            "osascript",
            "-e",
            f'set volume output volume {value}'
        ])
    except Exception as exc:
        return ActionResult(False, f"Failed: {exc}")

    return ActionResult(True, f"Brightness set to {value}%")

def set_volume(intent: Intent) -> ActionResult:
    value = int(intent.parameters.get("value", 50))

    try:
        subprocess.run([
            "osascript",
            "-e",
            f"set volume output volume {value}"
        ])
    except Exception as exc:
        return ActionResult(False, f"Failed: {exc}")

    return ActionResult(True, f"Volume set to {value}%")

def search_google(intent: Intent) -> ActionResult:
    query = intent.parameters.get("query", "")

    try:
        subprocess.Popen([
            "open",
            f"https://www.google.com/search?q={query}"
        ])
    except Exception as exc:
        return ActionResult(False, str(exc))

    return ActionResult(True, f"Searching Google for {query}")

def search_maps(intent: Intent) -> ActionResult:
    query = intent.parameters.get("query", "")

    subprocess.Popen([
        "open",
        f"https://www.google.com/maps/search/{query}"
    ])

    return ActionResult(True, f"Opening maps for {query}")

def open_app_dynamic(intent: Intent) -> ActionResult:
    app = intent.parameters.get("app", "")

    try:
        subprocess.Popen(["open", "-a", app])
    except Exception as exc:
        return ActionResult(False, f"App not found: {app}")

    return ActionResult(True, f"Opening {app}")

def open_folder(intent: Intent) -> ActionResult:
    folder = intent.parameters.get("folder_name", "")

    path = os.path.expanduser(f"~/Desktop/{folder}")

    subprocess.Popen(["open", path])

    return ActionResult(True, f"Opened folder {folder}")


def minimize_window(_: Intent) -> ActionResult:
    subprocess.run([
        "osascript",
        "-e",
        'tell application "System Events" to keystroke "m" using command down'
    ])
    return ActionResult(True, "Window minimized")

def maximize_window(_: Intent) -> ActionResult:
    subprocess.run([
        "osascript",
        "-e",
        'tell application "System Events" to keystroke "f" using command down'
    ])
    return ActionResult(True, "Window maximized")


def get_time(_: Intent) -> ActionResult:
    now = datetime.datetime.now()
    text = now.strftime("%A %I:%M %p")

    if pyttsx3:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    return ActionResult(True, text)


def execute_intent(intent: Intent) -> ActionResult:
    log(f"Executing action: {intent.name}")  # log intent name
    if intent.name == IntentName.CREATE_FOLDER:
        return create_folder(intent)
    if intent.name == IntentName.OPEN_BROWSER:
        return open_browser(intent)
    if intent.name == IntentName.OPEN_RECYCLE_BIN:
        return open_recycle_bin(intent)
    if intent.name == IntentName.CLOSE_WINDOW:
        return close_window(intent)
    if intent.name == IntentName.VOLUME_UP:
        return volume_up(intent)
    if intent.name == IntentName.VOLUME_DOWN:
        return volume_down(intent)
    if intent.name == IntentName.MUTE:
        return volume_mute(intent)
    if intent.name == IntentName.BRIGHTNESS_UP:
        return brightness_up(intent)
    if intent.name == IntentName.BRIGHTNESS_DOWN:
        return brightness_down(intent)
    if intent.name == IntentName.SET_VOLUME:
        return set_volume(intent) 
    if intent.name == IntentName.SET_BRIGHTNESS:
        return set_brightness(intent)
    if intent.name == IntentName.SEARCH_GOOGLE:
        return search_google(intent)
    if intent.name == IntentName.OPEN_APP_DYNAMIC:
        return open_app_dynamic(intent)
    if intent.name == IntentName.GET_TIME:
        return get_time(intent)
    if intent.name == IntentName.SEARCH_MAP:
        return search_maps(intent)
    if intent.name == IntentName.MINIMIZE_WINDOW:
        return minimize_window(intent)
    if intent.name == IntentName.MAXIMIZE_WINDOW:
        return maximize_window(intent)
    if intent.name == IntentName.OPEN_FOLDER:
        return open_folder(intent)
    elif intent.name == "START_GESTURE":
        return ActionResult(success=True, user_message="Switching to gesture mode")
    return ActionResult(False, "Command not recognized.")
