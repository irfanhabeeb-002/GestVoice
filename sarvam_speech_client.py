from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from config import get_settings
import certifi
import ssl

ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())


class SarvamClientError(Exception):
    pass


@dataclass
class TranscriptionResult:
    text: str


class SarvamClient:
    """
    Sarvam Speech-to-Text client.

    Notes:
    - We use `mode="translit"` by default so Malayalam gets Romanized output,
      which your NLU (`nlu.py`) is already tuned for.
    """

    # Sarvam STT REST endpoint for short (<= ~30s) synchronous requests.
    URL = "https://api.sarvam.ai/speech-to-text"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = (settings.sarvam_api_key or "").strip()
        if not self.api_key:
            raise SarvamClientError(
                "Missing Sarvam API key. Set `SARVAM_API_KEY` in your environment/.env."
            )

    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        language_code: str = "ml-IN",
        model: str = "saaras:v3",
        mode: str = "translit",
    ) -> TranscriptionResult:
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": model, "mode": mode, "language_code": language_code}
        headers = {"api-subscription-key": self.api_key}

        try:
            response = requests.post(
                self.URL,
                headers=headers,
                data=data,
                files=files,
                timeout=60,
            )

            # Sarvam returns JSON errors like: {"error": {"message": "..."}}
            if not response.ok:
                try:
                    body = response.json()
                    msg = body.get("error", {}).get("message") or str(body)
                except Exception:
                    msg = response.text
                raise SarvamClientError(f"Sarvam STT failed ({response.status_code}): {msg}")

            data = response.json()
            # API response uses `transcript` field (not `text`)
            text = data.get("transcript") or ""
            return TranscriptionResult(text=text.strip())
        except SarvamClientError:
            raise
        except Exception as exc:
            raise SarvamClientError(str(exc)) from exc