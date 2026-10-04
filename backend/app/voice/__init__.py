"""Voice processing integration package (Phase 7).

Components:
- Speech-to-Text Provider (AI4Bharat IndicWhisper / STTProvider)
- Clinical Observation Confirmation Boundary
- Text-to-Speech Provider (AI4Bharat Indic-TTS / TTSProvider)
"""

from backend.app.voice.providers import (
    MockSTTProvider,
    MockTTSProvider,
    STTProvider,
    STTResult,
    TTSProvider,
    TTSResult,
    get_stt_provider,
    get_tts_provider,
    reset_voice_providers,
    set_stt_provider,
    set_tts_provider,
)

__all__ = [
    "STTProvider",
    "TTSProvider",
    "STTResult",
    "TTSResult",
    "MockSTTProvider",
    "MockTTSProvider",
    "get_stt_provider",
    "set_stt_provider",
    "get_tts_provider",
    "set_tts_provider",
    "reset_voice_providers",
]
