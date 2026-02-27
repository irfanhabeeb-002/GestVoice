from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from audio_capture import record_until_stop, RecordingError
from nlu import parse_command
from actions import execute_intent, ActionResult
from speech_recognition_client import WhisperClient, WhisperClientError


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
        if self._listening:
            # User pressed again: request stop.
            self.status_var.set("Stopping...")
            self._stop_event.set()
            return

        self._listening = True
        self._stop_event.clear()
        self.status_var.set("Listening...")
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
            client = WhisperClient()
            result = client.transcribe(audio_bytes)
            transcript = result.text
        except WhisperClientError as exc:
            self._update_after_error(str(exc))
            return

        intent = parse_command(transcript)
        action_result: ActionResult = execute_intent(intent)

        def _update_ui() -> None:
            self.transcript_var.set(transcript or "(empty)")
            self.action_var.set(action_result.user_message)
            self.status_var.set("Done.")
            self.progress.stop()
            self.toggle_button.config(text="Start Listening", state="normal")
            self._listening = False

        self.root.after(0, _update_ui)

    def _update_after_error(self, message: str) -> None:
        def _ui() -> None:
            self.status_var.set("Error.")
            self.action_var.set(message)
            self.progress.stop()
            self.toggle_button.config(text="Start Listening", state="normal")
            self._listening = False

        self.root.after(0, _ui)


def main() -> None:
    root = tk.Tk()
    app = GestVoiceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

