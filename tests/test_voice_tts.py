"""Testes do modulo Text-to-Speech (TTS).

Valida inicializacao, sintese e reproducao com mocks, sem depender
de modelo real ou hardware de audio.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.tts import TTSError, TextToSpeech


class TestTextToSpeechInit:
    """Testes de inicializacao do TextToSpeech."""

    def test_init_defaults(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        assert tts.model_path is None
        assert tts.config_path is None
        assert tts._is_loaded is False
        assert tts._engine is None
        assert (tmp_path / "out").is_dir()

    def test_init_logs(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="jarvis.voice.tts"):
            TextToSpeech(output_dir=str(tmp_path / "out"))
        assert "TextToSpeech inicializado" in caplog.text


class TestTextToSpeechLoadModel:
    """Testes de carga do modelo Piper."""

    def test_load_model_success(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        with patch("piper.PiperVoice") as mock_voice:
            tts.load_model()
        assert tts._is_loaded is True
        assert tts._engine is mock_voice.load.return_value
        mock_voice.load.assert_called_once()

    def test_load_model_idempotent(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        with patch("piper.PiperVoice") as mock_voice:
            tts.load_model()
            tts.load_model()
        mock_voice.load.assert_called_once()

    def test_load_model_import_error(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        with patch("piper.PiperVoice", side_effect=ImportError("missing")):
            with pytest.raises(TTSError, match="piper-tts nao disponivel"):
                tts.load_model()

    def test_load_model_generic_error(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        with patch("piper.PiperVoice", side_effect=RuntimeError("boom")):
            with pytest.raises(TTSError, match="Nao foi possivel carregar"):
                tts.load_model()


class TestTextToSpeechSynthesize:
    """Testes de sintese de audio."""

    def test_synthesize_success(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        tts._is_loaded = True
        tts._engine = MagicMock()
        with patch("wave.open", MagicMock()):
            result = tts.synthesize("Olá mundo")
        assert result.endswith(".wav")
        tts._engine.synthesize_wav.assert_called_once()

    def test_synthesize_uses_cache_filename(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        tts._is_loaded = True
        tts._engine = MagicMock()
        text = "texto unico"
        expected_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        with patch("wave.open", MagicMock()):
            result = tts.synthesize(text)
        assert result.endswith(f"tts_{expected_hash}.wav")

    def test_synthesize_custom_output(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        tts._is_loaded = True
        tts._engine = MagicMock()
        custom = str(tmp_path / "custom.wav")
        with patch("wave.open", MagicMock()):
            result = tts.synthesize("hi", output_file=custom)
        assert result == custom

    def test_synthesize_empty_text_raises(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        tts._is_loaded = True
        tts._engine = MagicMock()
        with pytest.raises(TTSError, match="Texto vazio"):
            tts.synthesize("")

    def test_synthesize_not_loaded_raises(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        with pytest.raises(TTSError, match="Modelo TTS nao carregado"):
            tts.synthesize("hi")

    def test_synthesize_failure_wraps_error(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        tts._is_loaded = True
        engine = MagicMock()
        engine.synthesize_wav.side_effect = RuntimeError("fail")
        tts._engine = engine
        with patch("wave.open", MagicMock()):
            with pytest.raises(TTSError, match="Falha ao sintetizar texto"):
                tts.synthesize("hi")


class TestTextToSpeechSynthesizeAndPlay:
    """Testes de sintese e reproducao."""

    def test_synthesize_and_play_success(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        tts._is_loaded = True
        tts._engine = MagicMock()
        with patch("wave.open", MagicMock()), patch("jarvis.voice.tts.sd") as mock_sd, patch(
            "jarvis.voice.tts.sf"
        ) as mock_sf:
            mock_sf.read.return_value = (b"audio", 22050)
            tts.synthesize_and_play("Olá")
        mock_sd.play.assert_called_once()
        mock_sd.wait.assert_called_once()

    def test_synthesize_and_play_missing_deps(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        tts._is_loaded = True
        tts._engine = MagicMock()
        with patch("wave.open", MagicMock()), patch(
            "jarvis.voice.tts.sd", side_effect=ImportError("missing")
        ), patch("jarvis.voice.tts.sf"):
            with pytest.raises(TTSError, match="sounddevice ou soundfile nao disponivel"):
                tts.synthesize_and_play("Olá")

    def test_synthesize_and_play_failure_wraps_error(self, tmp_path: Path) -> None:
        tts = TextToSpeech(output_dir=str(tmp_path / "out"))
        tts._is_loaded = True
        tts._engine = MagicMock()
        with patch("wave.open", MagicMock()), patch("jarvis.voice.tts.sd") as mock_sd, patch(
            "jarvis.voice.tts.sf"
        ) as mock_sf:
            mock_sf.read.return_value = (b"audio", 22050)
            mock_sd.play.side_effect = RuntimeError("fail")
            with pytest.raises(TTSError, match="Falha ao reproduzir fala"):
                tts.synthesize_and_play("Olá")