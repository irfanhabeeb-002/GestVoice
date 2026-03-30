from __future__ import annotations

import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from audio_capture import record_until_stop, RecordingError
from nlu import parse_command
from actions import execute_intent, ActionResult
from speech_recognition_client import WhisperClient, WhisperClientError
from sarvam_speech_client import SarvamClient, SarvamClientError

LISTEN_DURATION_SECONDS = 4.0


class GestVoiceApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("GestVoice")
        # Comfortable default size where all content (including the
        # primary button) is visible without manual resizing.
        self.root.geometry("520x520")
        self.root.minsize(700, 400)

        self.status_var = tk.StringVar(value="Ready.")
        self.transcript_var = tk.StringVar(value="")
        self.action_var = tk.StringVar(value="")

        self._listening = False
        self._stop_event = threading.Event()

        self._build_ui()

    def _build_ui(self) -> None:
        # --- UI theme (minimal, product-like) --------------------------------
        # Design goals:
        # - Clean hierarchy: title → status → transcript → action result
        # - One strong primary action button
        # - Neutral background + subtle state accent (Listening/Processing/Done/Error)
        # - Use ttk widgets + a custom style to avoid default grey system look
        self.colors = {
            "bg": "#0B0B0C",          # near-black (Nike-like)
            "surface": "#111113",     # card background
            "text": "#F3F4F6",        # near-white
            "muted": "#A1A1AA",       # subtle labels
            "border": "#1F1F23",
            "accent": "#7C3AED",      # purple accent
            "good": "#22C55E",
            "warn": "#F59E0B",
            "bad": "#EF4444",
        }

        self.root.configure(bg=self.colors["bg"])

        self.fonts = self._load_fonts()
        self._configure_ttk_style()

        # Layout: a centered card with generous padding.
        outer = tk.Frame(self.root, bg=self.colors["bg"])
        outer.pack(fill="both", expand=True, padx=28, pady=28)

        card = tk.Frame(
            outer,
            bg=self.colors["surface"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        card.pack(fill="both", expand=True)

        content = tk.Frame(card, bg=self.colors["surface"])
        content.pack(fill="both", expand=True, padx=22, pady=20)

        # Title row
        title_row = tk.Frame(content, bg=self.colors["surface"])
        title_row.pack(fill="x")

        title = tk.Label(
            title_row,
            text="GestVoice",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=self.fonts["title"],
        )
        title.pack(side="left", anchor="w")

        subtitle = tk.Label(
            title_row,
            text="Voice assistant",
            bg=self.colors["surface"],
            fg=self.colors["muted"],
            font=self.fonts["muted"],
        )
        subtitle.pack(side="right", anchor="e")

        # Status block
        status_block = tk.Frame(content, bg=self.colors["surface"])
        status_block.pack(fill="x", pady=(14, 0))

        status_label = tk.Label(
            status_block,
            text="Status",
            bg=self.colors["surface"],
            fg=self.colors["muted"],
            font=self.fonts["muted"],
        )
        status_label.pack(anchor="w")

        self.status_value_label = tk.Label(
            status_block,
            textvariable=self.status_var,
            bg=self.colors["surface"],
            fg=self.colors["accent"],
            font=self.fonts["status"],
        )
        self.status_value_label.pack(anchor="w", pady=(2, 0))

        # Subtle progress bar (only animate when working).
        self.progress = ttk.Progressbar(content, mode="indeterminate", style="GV.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(10, 18))

        # Transcript block
        transcript_block = tk.Frame(content, bg=self.colors["surface"])
        transcript_block.pack(fill="x")

        transcript_label_title = tk.Label(
            transcript_block,
            text="Last transcript",
            bg=self.colors["surface"],
            fg=self.colors["muted"],
            font=self.fonts["muted"],
        )
        transcript_label_title.pack(anchor="w")

        self.transcript_label = tk.Label(
            transcript_block,
            textvariable=self.transcript_var,
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=self.fonts["body"],
            wraplength=640,
            justify="left",
        )
        self.transcript_label.pack(anchor="w", pady=(6, 0))

        # Action/result block
        action_block = tk.Frame(content, bg=self.colors["surface"])
        action_block.pack(fill="x", pady=(18, 0))

        action_label_title = tk.Label(
            action_block,
            text="Result",
            bg=self.colors["surface"],
            fg=self.colors["muted"],
            font=self.fonts["muted"],
        )
        action_label_title.pack(anchor="w")

        self.action_label = tk.Label(
            action_block,
            textvariable=self.action_var,
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=self.fonts["body"],
            wraplength=640,
            justify="left",
        )
        self.action_label.pack(anchor="w", pady=(6, 0))

        # Footer with one primary button, centered.
        footer = tk.Frame(content, bg=self.colors["surface"])
        footer.pack(fill="x", pady=(22, 0))

        self.toggle_button = ttk.Button(
            footer,
            text="Start Listening",
            command=self.on_toggle_listening,
            style="GV.Primary.TButton",
        )
        self.toggle_button.pack(anchor="center", ipadx=10, ipady=6)

        # Keep status styling in sync with status text.
        self.status_var.trace_add("write", lambda *_: self._apply_status_style(self.status_var.get()))
        self._apply_status_style(self.status_var.get())

    def _load_fonts(self) -> dict[str, tkfont.Font]:
        """
        Safe font selection:
        - Prefer Inter if installed on the system
        - Otherwise fall back to common Windows UI fonts
        """
        families = set(tkfont.families(self.root))
        preferred = ["Inter", "Segoe UI", "Calibri", "Arial"]
        family = next((f for f in preferred if f in families), "TkDefaultFont")

        return {
            "title": tkfont.Font(family=family, size=20, weight="bold"),
            "status": tkfont.Font(family=family, size=13, weight="bold"),
            "body": tkfont.Font(family=family, size=12),
            "muted": tkfont.Font(family=family, size=10),
        }

    def _configure_ttk_style(self) -> None:
        style = ttk.Style(self.root)

        # 'clam' is a reliable base for custom styling on Windows.
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "GV.Primary.TButton",
            font=self.fonts["body"],
            foreground=self.colors["text"],
            background=self.colors["accent"],
            bordercolor=self.colors["accent"],
            focusthickness=0,
            padding=(16, 10),
            relief="flat",
        )
        style.map(
            "GV.Primary.TButton",
            background=[
                ("pressed", "#6D28D9"),
                ("active", "#8B5CF6"),
                ("disabled", "#2A2A2E"),
            ],
            foreground=[("disabled", self.colors["muted"])],
        )

        style.configure(
            "GV.Horizontal.TProgressbar",
            troughcolor=self.colors["border"],
            background=self.colors["accent"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["accent"],
            darkcolor=self.colors["accent"],
        )

    def _apply_status_style(self, status_text: str) -> None:
        """
        Subtle accent color per state to improve clarity without visual noise.
        """
        s = (status_text or "").lower()
        if "listening" in s:
            color = self.colors["accent"]
        elif "processing" in s:
            color = self.colors["warn"]
        elif "done" in s or "ready" in s:
            color = self.colors["good"]
        elif "error" in s:
            color = self.colors["bad"]
        else:
            color = self.colors["accent"]
        self.status_value_label.configure(fg=color)

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

        used_stt = "unknown"
        transcript_display = "(empty)"
        try:
            self.root.after(0, lambda: self.status_var.set("Processing (Sarvam)..."))
            client = SarvamClient()
            # 1) Display Malayalam script to the user.
            display_result = client.transcribe(
                audio_bytes,
                language_code="ml-IN",
                mode="transcribe",
            )
            transcript_display = display_result.text

            # 2) Use Romanized output for more reliable matching to your rules.
            nlu_result = client.transcribe(
                audio_bytes,
                language_code="ml-IN",
                mode="translit",
            )
            transcript = nlu_result.text
            used_stt = "Sarvam"
        except Exception as exc:
            # fallback to Whisper if Sarvam fails
            self.root.after(0, lambda: self.status_var.set("Processing (Whisper)..."))
            client = WhisperClient()
            result = client.transcribe(audio_bytes, language_hint="ml")
            transcript_display = result.text
            transcript = transcript_display
            used_stt = "Whisper"
            sarvam_error = str(exc)

        intent = parse_command(transcript)
        action_result: ActionResult = execute_intent(intent)

        def _update_ui() -> None:
            self.transcript_var.set(transcript_display or "(empty)")
            self.action_var.set(action_result.user_message)
            # Show which engine produced the transcript.
            self.status_var.set(f"Done ({used_stt}).")
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

