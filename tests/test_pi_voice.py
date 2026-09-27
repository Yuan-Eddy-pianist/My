"""Regression checks for Pi's local voice-to-draft transcription helper."""

import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from pi_voice.transcribe import has_speech_signal, transcribe


ROOT = Path(__file__).resolve().parents[1]


class PiVoiceTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "data" / "tmp").mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / "data" / "tmp")
        self.addCleanup(self.tmp.cleanup)
        self.wav = Path(self.tmp.name) / "sample.wav"

    def write_wav(self, samples):
        with wave.open(str(self.wav), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    def test_empty_and_silent_recording_rejected_before_whisper(self):
        self.write_wav([0] * 16000)
        self.assertFalse(has_speech_signal(self.wav))
        with self.assertRaisesRegex(ValueError, "No clear speech"):
            transcribe(self.wav)
        self.write_wav([1200] * 1000)
        self.assertFalse(has_speech_signal(self.wav))

    def test_waveform_above_noise_floor_detected(self):
        samples = [0] * 16000 + [int(1600 * math.sin(n / 10)) for n in range(1600)]
        self.write_wav(samples)
        self.assertTrue(has_speech_signal(self.wav))

    def test_invalid_wav_rejected(self):
        self.wav.write_bytes(b"not a WAV")
        with self.assertRaises((ValueError, EOFError, wave.Error)):
            transcribe(self.wav)


if __name__ == "__main__":
    unittest.main()
