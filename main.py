from __future__ import annotations
from Gesture_Controller import run_gesture
import threading
import tkinter as tk
from tkinter import ttk
from logger import log
from audio_capture import record_until_stop, RecordingError
from nlu import parse_command
from actions import execute_intent, ActionResult
from speech_recognition_client import WhisperClient, WhisperClientError
from sarvam_speech_client import SarvamClient, SarvamClientError
from datetime import datetime, timedelta


LISTEN_DURATION_SECONDS = 4.0


class GestVoiceApp:
    
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("GestVoice")
        self.root.geometry("600x320")

        self.status_var = tk.StringVar(value="Ready.")
        self.transcript_var = tk.StringVar(value="")
        self.action_var = tk.StringVar(value="")

        self._listening = False
        self._stop_event = threading.Event()
        self.gesture_mode_active = False
        self.voice_active = True
        self.whisper_client = WhisperClient()   
        try:
            self.sarvam_client = SarvamClient()
        except SarvamClientError as e:
            # Keep Whisper functional even when Sarvam is not configured.
            self.sarvam_client = None
            log(f"Sarvam unavailable: {e}")
        self._build_ui()

    def _build_ui(self) -> None:
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        status_label = tk.Label(frame, text="Status:")
        status_label.pack(anchor="w")

        status_value_label = tk.Label(frame, textvariable=self.status_var, fg="blue")
        status_value_label.pack(anchor="w")

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill="x", pady=(5, 10))

        transcript_label_title = tk.Label(frame, text="Last transcript:")
        transcript_label_title.pack(anchor="w", pady=(10, 0))
        transcript_label = tk.Label(frame, textvariable=self.transcript_var, wraplength=540, justify="left")
        transcript_label.pack(anchor="w")

        action_label_title = tk.Label(frame, text="Last action:")
        action_label_title.pack(anchor="w", pady=(10, 0))
        action_label = tk.Label(frame, textvariable=self.action_var, wraplength=540, justify="left")
        action_label.pack(anchor="w")

        button_frame = tk.Frame(frame, pady=20)
        button_frame.pack()

        self.toggle_button = tk.Button(button_frame, text="Start Listening", command=self.on_toggle_listening)
        self.toggle_button.pack(side="left", padx=10)

    def on_toggle_listening(self) -> None:
        
        if not self.voice_active:
            log("Voice system is inactive")
            self.status_var.set("Voice is disabled. Restart app to use again.")
            return
        
        if self._listening and self.voice_active:
            log("Stopping voice listening")
            self.status_var.set("Stopping...")
            self._stop_event.set()
            return


        self._listening = True
        self._stop_event.clear()
        self.status_var.set("Listening...")
        log("Voice listening started") 
        self.toggle_button.config(text="Stop Listening", state="normal")
        self.progress.start(10)

        threading.Thread(target=self._listen_and_process, daemon=True).start()

    def _listen_and_process(self) -> None:
        try:
            audio_bytes = record_until_stop(self._stop_event, max_seconds=LISTEN_DURATION_SECONDS)
        except RecordingError as exc:
            self._update_after_error(f"Recording failed: {exc}")
            return

        # Update status to show we are now processing the audio
        self.root.after(0, lambda: self.status_var.set("Processing..."))

        try:
            if self.sarvam_client is None:
                raise SarvamClientError("Sarvam client not initialized")

            log("Using Sarvam STT...")

            # 🔥 1. UI DISPLAY (Malayalam script)
            display_result = self.sarvam_client.transcribe(
                audio_bytes,
                language_code="ml-IN",
                mode="transcribe",
            )
            transcript_display = display_result.text

            # 🔥 2. NLU INPUT (Romanized)
            nlu_result = self.sarvam_client.transcribe(
                audio_bytes,
                language_code="ml-IN",
                mode="translit",
            )
            transcript = nlu_result.text

            log(f"Sarvam Display: {transcript_display}")
            log(f"Sarvam NLU: {transcript}")

        except SarvamClientError as e:
            log(f"Sarvam failed, falling back to Whisper: {e}")
            self.status_var.set("Processing (Whisper fallback)...")

            try:
                result = self.whisper_client.transcribe(audio_bytes)
                transcript = result.text
                transcript_display = result.text  # fallback same
                log(f"[FALLBACK ACTIVE] Whisper Transcript: {transcript}")
            except WhisperClientError as exc:
                self._update_after_error(str(exc))
                return

        log(f"Transcript: {transcript}")   # log transcript

        if not transcript_display or len(transcript_display.strip()) < 2:
            log("Ignored empty/noise input")
            self._update_after_error("No speech detected")
            return


        intent = parse_command(transcript)
        log(f"Intent detected: {intent.name}")


        if intent.name == "START_GESTURE" and not self.gesture_mode_active:
            log("Gesture mode activated. Use hand gestures to control.")
            self.gesture_mode_active = True

            self.status_var.set("Switching to gesture mode...")
            self.root.update()

            self.status_var.set("Gesture Mode Active")
            self.action_var.set("Use gesture. Show exit gesture to return.")

            # 🔥 HIDE VOICE WINDOW
            self.root.iconify()

            start_gesture()
            return

        if intent.name == "EXIT":
            log("Voice exit command detected")

            stop_gesture()   # 🔥 ensure gesture also stops

            self.voice_active = False
            self._stop_event.set()
            self._listening = False

            self.status_var.set("Shutting down...")
            self.action_var.set("Closing application")

            self.progress.stop()

            self.root.after(500, self.root.destroy)

            return

        print("🎯 Intent: ", intent)

        try:
            action_result: ActionResult = execute_intent(intent)
        except Exception as e:
            log(f"Execution error: {e}")
            self._update_after_error("Action failed")
            return

        if action_result.success:
            log(f"Response: {action_result.user_message}")
        else:
            log("Action failed")

        
        self.root.after(0, lambda ar=action_result: self._update_ui(transcript_display, ar))


    def _update_ui(self, transcript, action_result: ActionResult) -> None:
            self.transcript_var.set(transcript or "(empty)")
            self.action_var.set(action_result.user_message)
            self.status_var.set("Done.")
            self.progress.stop()
            self.toggle_button.config(text="Start Listening", state="normal")
            self._listening = False
            

    def _update_after_error(self, message: str) -> None:
        def _ui() -> None:
            self.status_var.set("Error.")
            self.action_var.set(message)
            self.progress.stop()
            self.toggle_button.config(text="Start Listening", state="normal")
            self._listening = False

        self.root.after(0, _ui)

def check_gesture_process(app):
    global gesture_process

    if gesture_process and gesture_process.poll() is not None:
        log("Gesture ended → resuming voice")

        gesture_process = None
        app.gesture_mode_active = False

        # 🔥 RESTORE WINDOW
        app.root.deiconify()
        app.root.lift()
        app.root.attributes('-topmost', True)
        app.root.after(100, lambda: app.root.attributes('-topmost', False))

        # UI update
        app.status_var.set("Back to Voice Mode")
        app.action_var.set("Gesture mode closed")

        # 🔥 AUTO RESUME
        app._listening = False
        app.status_var.set("Back to Voice Mode (Click to start listening)")
        app.action_var.set("Gesture mode closed")
        app.progress.stop()
        app.toggle_button.config(text="Start Listening", state="normal")

    app.root.after(1000, lambda: check_gesture_process(app))
    

import subprocess
import sys

gesture_process = None

def start_gesture():
    global gesture_process

    if gesture_process is None or gesture_process.poll() is not None:
        gesture_process = subprocess.Popen([sys.executable, "Gesture_Controller.py"])


def stop_gesture():
    global gesture_process
    if gesture_process:
        gesture_process.terminate()
        gesture_process = None


def main():
    root = tk.Tk()
    app = GestVoiceApp(root)

    # 🔥 DELAYED FOCUS FIX
    def bring_to_front():
        root.deiconify()
        root.lift()
        root.attributes('-topmost', True)
        root.after(200, lambda: root.attributes('-topmost', False))
        root.focus_force()

    root.after(300, bring_to_front)

    check_gesture_process(app)

    root.mainloop()

if __name__ == "__main__":
    main()