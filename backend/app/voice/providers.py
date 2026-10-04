"""Voice Provider Abstractions for Speech-to-Text and Text-to-Speech (Phase 7).

Decouples the public API contract from underlying speech technologies (e.g. AI4Bharat IndicWhisper,
AI4Bharat Indic-TTS, Sarvam AI).

Enforces:
- Stable provider-neutral interface.
- Provider errors do not leak internal credentials or raw tracebacks to the client.
- Testability via deterministic mock providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from backend.app.schemas.voice import VoiceLanguage


@dataclass
class STTResult:
    """Internal result produced by a Speech-to-Text provider."""
    transcript: str
    language: VoiceLanguage
    detected_language: VoiceLanguage
    confidence: float
    duration_seconds: float


@dataclass
class TTSResult:
    """Internal result produced by a Text-to-Speech provider."""
    audio_bytes: bytes
    mime_type: str
    language: VoiceLanguage
    duration_seconds: float


class STTProvider(ABC):
    """Abstract provider interface for Speech-to-Text transcription."""

    @abstractmethod
    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        language: VoiceLanguage,
    ) -> STTResult:
        """Transcribe audio bytes in the specified language to text.
        
        Raises:
            Exception if transcription fails (caught by service boundary).
        """
        pass


class TTSProvider(ABC):
    """Abstract provider interface for Text-to-Speech synthesis."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        language: VoiceLanguage,
        output_format: str,
    ) -> TTSResult:
        """Synthesize input text in the specified language into audio bytes.
        
        Raises:
            Exception if synthesis fails (caught by service boundary).
        """
        pass


class MockSTTProvider(STTProvider):
    """Deterministic default/mock STT provider for offline verification and testing."""

    def __init__(self):
        self.should_fail: bool = False
        self.failure_error: str = "Simulated STT provider upstream failure"
        self.default_transcript: str = "I have been experiencing a mild headache and tiredness."

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        language: VoiceLanguage,
    ) -> STTResult:
        if self.should_fail:
            raise RuntimeError(self.failure_error)

        # Estimate duration roughly based on payload size (or default 3.5s)
        duration = max(1.0, round(len(audio_bytes) / 32000.0, 2))
        if duration > 120.0:
            duration = 120.0

        return STTResult(
            transcript=self.default_transcript,
            language=language,
            detected_language=language,
            confidence=0.96,
            duration_seconds=duration,
        )


class MockTTSProvider(TTSProvider):
    """Deterministic default/mock TTS provider for offline verification and testing."""

    def __init__(self):
        self.should_fail: bool = False
        self.failure_error: str = "Simulated TTS provider upstream failure"

    def synthesize(
        self,
        text: str,
        language: VoiceLanguage,
        output_format: str,
    ) -> TTSResult:
        if self.should_fail:
            raise RuntimeError(self.failure_error)

        # Minimal standard WAV header (44 bytes) + 100 bytes silence
        sample_rate = 16000
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = 200
        total_size = 36 + data_size

        wav_header = (
            b"RIFF" + total_size.to_bytes(4, "little") +
            b"WAVEfmt " + (16).to_bytes(4, "little") + (1).to_bytes(2, "little") +
            num_channels.to_bytes(2, "little") + sample_rate.to_bytes(4, "little") +
            byte_rate.to_bytes(4, "little") + block_align.to_bytes(2, "little") +
            bits_per_sample.to_bytes(2, "little") + b"data" + data_size.to_bytes(4, "little") +
            (b"\x00" * data_size)
        )

        duration = max(1.0, round(len(text) * 0.06, 2))

        return TTSResult(
            audio_bytes=wav_header,
            mime_type=output_format,
            language=language,
            duration_seconds=duration,
        )


# Global provider instances
_default_stt_provider = MockSTTProvider()
_default_tts_provider = MockTTSProvider()

_active_stt_provider: STTProvider = _default_stt_provider
_active_tts_provider: TTSProvider = _default_tts_provider


def get_stt_provider() -> STTProvider:
    """Return active Speech-to-Text provider."""
    return _active_stt_provider


def set_stt_provider(provider: STTProvider):
    """Override Speech-to-Text provider (used for testing or switching vendors)."""
    global _active_stt_provider
    _active_stt_provider = provider


def get_tts_provider() -> TTSProvider:
    """Return active Text-to-Speech provider."""
    return _active_tts_provider


def set_tts_provider(provider: TTSProvider):
    """Override Text-to-Speech provider (used for testing or switching vendors)."""
    global _active_tts_provider
    _active_tts_provider = provider


def reset_voice_providers():
    """Reset voice providers to default mock implementations."""
    global _active_stt_provider, _active_tts_provider
    _active_stt_provider = _default_stt_provider
    _active_tts_provider = _default_tts_provider
    _default_stt_provider.should_fail = False
    _default_tts_provider.should_fail = False
