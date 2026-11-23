"""Fixtures e configuração compartilhada para os testes do J.A.R.V.I.S."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fake_whisper_model():
    """Retorna um mock do modelo Whisper com transcribe falso."""
    model = MagicMock()
    segment1 = SimpleNamespace(text="Olá")
    segment2 = SimpleNamespace(text="mundo")
    model.transcribe.return_value = ([segment1, segment2], None)
    return model


@pytest.fixture
def fake_piper_voice():
    """Retorna um mock do PiperVoice com synthesize_wav falso."""
    engine = MagicMock()
    engine.synthesize_wav.return_value = None
    return engine


@pytest.fixture
def fake_sounddevice():
    """Retorna um mock do sounddevice."""
    sd = MagicMock()
    sd.rec.return_value = [[0.0] * 16000]
    sd.query_devices.return_value = [
        {"name": "Mic", "max_input_channels": 1, "max_output_channels": 0, "default_samplerate": 16000},
        {"name": "Speakers", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100},
    ]
    return sd


@pytest.fixture
def fake_soundfile():
    """Retorna um mock do soundfile."""
    sf = MagicMock()
    sf.read.return_value = ([0.0] * 16000, 16000)
    return sf