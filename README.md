# GestVoice

GestVoice is a desktop assistant that combines **voice commands** (English and Malayalam) with an optional **hand-gesture** mode. It uses a **local [faster-whisper](https://github.com/SYSTRAN/faster-whisper)** model for speech-to-text (no cloud API for transcription), maps text to intents, and runs system actions.

## Features

- **Voice mode** — Tkinter UI: record from the microphone, transcribe, parse intent, execute actions.
- **Gesture mode** — Say a start-gesture phrase (see `nlu.py`) to launch `Gesture_Controller.py` in a separate process; the main window minimizes until the gesture session ends.
- **Intents** — Folder creation, browser/maps search, open apps/folders, window controls, volume and brightness (implementation is **macOS-oriented** in `actions.py` via `osascript` / `open`).
- **Gestures** — MediaPipe hands + OpenCV; on **Windows**, volume/brightness in the gesture controller use `pycaw` and `screen-brightness-control`.

## Project layout

| File | Role |
|------|------|
| `main.py` | Tkinter app: recording → Whisper → NLU → actions; spawns gesture subprocess. |
| `Gesture_Controller.py` | Webcam hand gestures and desktop control. |
| `audio_capture.py` | Microphone capture to WAV bytes (`sounddevice`, `scipy`). |
| `speech_recognition_client.py` | Local `faster-whisper` wrapper. |
| `nlu.py` | Rule-based English/Malayalam command → intent. |
| `actions.py` | Intent dispatcher and OS-specific actions. |
| `config.py` | `python-dotenv` settings (`GV_BASE_FOLDER`, `GV_HOMEPAGE_URL`, etc.). |
| `requirements.txt` | Dependencies (with Windows-only markers where needed). |

## Requirements

- Python 3.10+ recommended.
- Microphone access; first run downloads the Whisper model (cached by the library).
- **macOS**: Accessibility / Automation permissions may be needed for `osascript` key events.
- **Gesture mode**: webcam; on Apple Silicon, if stock `mediapipe` fails to install, try a maintained build such as `mediapipe-silicon` for your platform.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Optional `.env` in the project root:

```bash
GV_BASE_FOLDER=/path/to/GestVoice
GV_HOMEPAGE_URL=https://www.google.com
```

## Run

```bash
python main.py
```

Use **Start Listening** / **Stop Listening**, then speak commands. To enter gesture mode, use the phrase configured for `START_GESTURE` in `nlu.py`.

## Tags (release markers)

This repository may be tagged for milestones, for example: `integrated`, `MVP`, `working-condition`.
