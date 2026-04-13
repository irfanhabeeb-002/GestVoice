from __future__ import annotations

import io
import threading
from typing import Optional
from logger import log
import sounddevice as sd
import wave
import numpy as np


DEFAULT_SAMPLE_RATE = 16_000
DEFAULT_CHANNELS = 1


class RecordingError(Exception):
    pass


def record_until_stop(
    stop_event: threading.Event,
    max_seconds: float = 8.0,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> bytes:
    """
    Record audio from the default microphone until stop_event is set
    or max_seconds is reached. Returns WAV bytes.
    """
    frames: list[np.ndarray] = []
    block_size = 1024
    max_frames = int(max_seconds * sample_rate)
    collected = 0

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=DEFAULT_CHANNELS,
            dtype="float32",
            blocksize=block_size,
        ) as stream:
            while not stop_event.is_set() and collected < max_frames:
                data, _overflowed = stream.read(block_size)
                frames.append(data.copy())
                collected += data.shape[0]
    except Exception as exc:  # pragma: no cover - hardware specific
        raise RecordingError(f"Error while recording audio: {exc}") from exc

    if not frames:
        raise RecordingError("No audio data captured.")

    audio = np.concatenate(frames, axis=0)
    audio_int16 = np.int16(audio * 32767)

    with io.BytesIO() as buffer:
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        return buffer.getvalue()