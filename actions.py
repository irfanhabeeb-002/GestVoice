from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass

import pyautogui
import screen_brightness_control as sbc

from config import get_settings
from nlu import Intent, IntentName


@dataclass
class ActionResult:
    success: bool
    user_message: str


def _ensure_base_folder() -> str:
    settings = get_settings()
    os.makedirs(settings.base_folder_path, exist_ok=True)
    return settings.base_folder_path


def create_folder(intent: Intent) -> ActionResult:
    settings = get_settings()
    base_path = _ensure_base_folder()
    folder_name = intent.parameters.get("folder_name")
    if not folder_name:
        folder_name = time.strftime("Folder_%Y%m%d_%H%M%S")

    safe_name = "".join(c for c in folder_name if c not in r"<>:\"/\\|?*")
    path = os.path.join(base_path, safe_name or "NewFolder")
    os.makedirs(path, exist_ok=True)

    try:
        subprocess.Popen(["explorer", path])
    except Exception:
        pass

    return ActionResult(True, f"Folder created at {path}")


def open_browser(_: Intent) -> ActionResult:
    settings = get_settings()
    try:
        subprocess.Popen(["cmd", "/c", "start", "", settings.homepage_url], shell=True)
    except Exception as exc:
        return ActionResult(False, f"Failed to open browser: {exc}")
    return ActionResult(True, "Browser opened.")


def open_recycle_bin(_: Intent) -> ActionResult:
    try:
        subprocess.Popen(["explorer", "shell:RecycleBinFolder"])
    except Exception as exc:
        return ActionResult(False, f"Failed to open recycle bin: {exc}")
    return ActionResult(True, "Recycle bin opened.")


def close_window(_: Intent) -> ActionResult:
    try:
        pyautogui.hotkey("alt", "f4")
    except Exception as exc:
        return ActionResult(False, f"Failed to close window: {exc}")
    return ActionResult(True, "Active window closed.")


def volume_up(_: Intent) -> ActionResult:
    try:
        pyautogui.press("volumeup")
    except Exception as exc:
        return ActionResult(False, f"Failed to increase volume: {exc}")
    return ActionResult(True, "Volume increased.")


def volume_down(_: Intent) -> ActionResult:
    try:
        pyautogui.press("volumedown")
    except Exception as exc:
        return ActionResult(False, f"Failed to decrease volume: {exc}")
    return ActionResult(True, "Volume decreased.")


def volume_mute(_: Intent) -> ActionResult:
    try:
        pyautogui.press("volumemute")
    except Exception as exc:
        return ActionResult(False, f"Failed to mute volume: {exc}")
    return ActionResult(True, "Volume muted or unmuted.")


def brightness_up(_: Intent) -> ActionResult:
    try:
        current = sbc.get_brightness(display=0)[0]
        sbc.set_brightness(min(current + 10, 100), display=0)
    except Exception as exc:
        return ActionResult(False, f"Failed to increase brightness: {exc}")
    return ActionResult(True, "Brightness increased.")


def brightness_down(_: Intent) -> ActionResult:
    try:
        current = sbc.get_brightness(display=0)[0]
        sbc.set_brightness(max(current - 10, 0), display=0)
    except Exception as exc:
        return ActionResult(False, f"Failed to decrease brightness: {exc}")
    return ActionResult(True, "Brightness decreased.")


def execute_intent(intent: Intent) -> ActionResult:
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

    return ActionResult(False, "Command not recognized.")

