#!/usr/bin/env python3
"""Transcribe a Pi microphone WAV through My's existing in-process Whisper implementation.

No server endpoints, inbox jobs, network transcription, or agent calls. Stdout is
reserved for the transcript; model diagnostics and exceptions go to stderr.
"""

from __future__ import annotations

import contextlib
import os
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def has_speech_signal(path: Path) -> bool:
    """Reject digital silence / empty recordings before asking Whisper (which can hallucinate)."""
    from array import array

    with wave.open(str(path), "rb") as audio:
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or audio.getframerate() != 16000:
            raise ValueError("Expected 16-kHz mono PCM microphone recording")
        if audio.getnframes() < 16000 // 3:
            return False
        # Require at least one 100-ms interval louder than about -42 dBFS.
        # A global average would reject a short phrase in a longer recording.
        while chunk := audio.readframes(1600):
            samples = array("h")
            samples.frombytes(chunk)
            if samples and sum(value * value for value in samples) >= 260**2 * len(samples):
                return True
    return False


def transcribe(path: Path) -> str:
    if not has_speech_signal(path):
        raise ValueError("No clear speech detected (silence or recording too short)")
    # MLX Whisper can hallucinate on room noise even if the waveform is nonzero.
    # Reuse the local Silero VAD bundled with My's faster-whisper dependency to
    # ensure there is actual speech before running either Whisper backend.
    from faster_whisper.audio import decode_audio
    from faster_whisper.vad import VadOptions, get_speech_timestamps

    if not get_speech_timestamps(decode_audio(str(path)), VadOptions(min_silence_duration_ms=500)):
        raise ValueError("No clear speech detected (voice activity check)")
    # serve.py's transcribe_path uses the same MLX model and CPU fallback as My.
    # Redirect its model-loading prints so stdout remains a single transcript.
    with contextlib.redirect_stdout(sys.stderr):
        from serve import transcribe_path

        text = transcribe_path(str(path)).strip()
    if not text:
        raise ValueError("No clear speech detected")
    return text


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("Usage: transcribe.py recording.wav")
        print(transcribe(Path(sys.argv[1])))
    except Exception as exc:
        print(f"Voice transcription failed: {exc}", file=sys.stderr)
        sys.exit(1)
