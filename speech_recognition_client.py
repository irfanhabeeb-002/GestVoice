from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import os
import tempfile
from faster_whisper import WhisperModel
from logger import log

class WhisperClientError(Exception):
    pass


@dataclass
class TranscriptionResult:
    text: str


class WhisperClient:
    """
    Thin wrapper around a local faster-whisper model for transcription.
    """

    def __init__(self, model_size: str = "small", device: Optional[str] = None) -> None:
        """
        Initialise the local Whisper model.

        - model_size: e.g. 'tiny', 'base', 'small', 'medium'.
        - device: 'cpu' or 'cuda'. Defaults to CPU.
        """
        device = device or "cpu"
        try:
            self._model = WhisperModel(
                model_size,
                device=device,
                compute_type="int8" if device == "cpu" else "float16",
            )
        except Exception as exc:  # pragma: no cover - model download / hardware specific
            raise WhisperClientError(f"Failed to load faster-whisper model: {exc}") from exc

    def transcribe(self, audio_bytes: bytes, language_hint: str = "ml") -> TranscriptionResult:
        """
        Transcribe the given WAV bytes using the local faster-whisper model.
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            segments, _info = self._model.transcribe(
                tmp_path,
                language=language_hint,
                beam_size=5,
            )

            pieces = [segment.text.strip() for segment in segments]
            text = " ".join(piece for piece in pieces if piece)
        except Exception as exc:  # pragma: no cover - transcription specific
            raise WhisperClientError(f"Error while running local Whisper transcription: {exc}") from exc
        finally:
            try:
                if "tmp_path" in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

        return TranscriptionResult(text=text.strip())

