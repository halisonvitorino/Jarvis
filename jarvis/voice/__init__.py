"""
J.A.R.V.I.S Voice Assistant - Phase 3

Modulo de voz para interacao via microfone e alto-falante.
Suporta Speech-to-Text (STT), Text-to-Speech (TTS) e Wake Word detection.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Modular: cada responsabilidade tem sua classe
- Testável: métodos puros com entradas/saídas explícitas
- Logado: todas as operações críticas têm logging
- Substituível: motores de voz podem ser trocados sem alterar o core
"""

from .stt import SpeechToText, STTError
from .tts import TextToSpeech, TTSError
from .wake_word import WakeWordDetector, WakeWordError

__all__ = [
    "SpeechToText",
    "STTError",
    "TextToSpeech",
    "TTSError",
    "WakeWordDetector",
    "WakeWordError",
]
