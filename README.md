# GestVoice – Malayalam Voice-Controlled Desktop Assistant

GestVoice is a small Python desktop GUI that listens for Malayalam (and simple English) voice commands, uses a **local faster-whisper model** for transcription (no API key or internet required after model download), maps the recognized text to intents, and performs basic actions on Windows such as:

- Creating a folder on your Desktop (or a configured base path).
- Opening the web browser.
- Opening the Recycle Bin.
- Closing the active window.
- Adjusting volume (up / down / mute).
- Adjusting screen brightness (up / down, on supported hardware).

## Project structure

- `main.py` – Tkinter GUI, orchestrates recording → transcription → intent → action.
- `audio_capture.py` – Functions for recording audio from the microphone.
- `speech_recognition_client.py` – Local faster-whisper client wrapper.
- `nlu.py` – Rule-based Malayalam/English command parser that turns text into intents.
- `actions.py` – Windows-specific implementations of system actions and dispatcher.
- `config.py` – Loads environment-based configuration (API key, base folder, homepage).
- `requirements.txt` – Python dependencies.

## Setup

1. **Create and activate a virtual environment** (recommended).
2. Install dependencies (this will also download the faster-whisper model the first time you run the app):

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Configure base folder and homepage via `.env` next to `config.py`:

   ```bash
   GV_BASE_FOLDER=C:\\Users\\<you>\\Desktop\\GestVoice
   GV_HOMEPAGE_URL=https://www.google.com
   ```

## Running the app

From the project directory:

```bash
python main.py
```

The window will open with a **Start Listening** button. When you click it, the app:

1. Records a short audio clip from the default microphone.
2. Runs the local faster-whisper model for transcription (Malayalam-focused).
3. Parses the recognized text into a command.
4. Executes the corresponding action on your computer.

The last transcript and action result are shown in the window. Any errors (e.g., missing API key, microphone problems) are also displayed.

