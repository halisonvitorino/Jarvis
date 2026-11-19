"""Testes do modulo Speech-to-Text (STT).

Valida inicializacao, tratamento de erros e transcricoes com mocks,
sem depender de hardware ou modelo real.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.stt import STTError, SpeechToText


class TestSpeechToTextInit:
    """Testes de inicializacao do SpeechToText."""

    def test_init_defaults(self) -> None:
        stt = SpeechToText()
        assert stt.model_size == "base"
        assert stt.language is None
        assert stt.compute_type == "int8"
        assert stt._is_loaded is False
        assert stt._model is None

    def test_init_custom_params(self) -> None:
        stt = SpeechToText(model_size="small", language="pt", compute_type="float16")
        assert stt.model_size == "small"
        assert stt.language == "pt"
        assert stt.compute_type == "float16"

    def test_init_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="jarvis.voice.stt"):
            SpeechToText(model_size="tiny")
        assert "SpeechToText inicializado" in caplog.text


class TestSpeechToTextLoadModel:
    """Testes de carga do modelo Whisper."""

    def test_load_model_success(self) -> None:
        stt = SpeechToText()
        with patch("faster_whisper.WhisperModel") as mock_model:
            stt.load_model()
        assert stt._is_loaded is True
        assert stt._model is mock_model.return_value
        mock_model.assert_called_once_with("base", compute_type="int8")

    def test_load_model_idempotent(self) -> None:
        stt = SpeechToText()
        with patch("faster_whisper.WhisperModel") as mock_model:
            stt.load_model()
            stt.load_model()
        mock_model.assert_called_once()

    def test_load_model_import_error(self) -> None:
        stt = SpeechToText()
        with patch("faster_whisper.WhisperModel", side_effect=ImportError("missing")):
            with pytest.raises(STTError, match="faster-whisper nao disponivel"):
                stt.load_model()
        assert stt._is_loaded is False

    def test_load_model_generic_error(self) -> None:
        stt = SpeechToText()
        with patch("faster_whisper.WhisperModel", side_effect=RuntimeError("boom")):
            with pytest.raises(STTError, match="Nao foi possivel carregar"):
                stt.load_model()


class TestSpeechToTextTranscribe:
    """Testes de transcicao de audio."""

    def _make_stt(self, segments_text: list[str]) -> SpeechToText:
        stt = SpeechToText()
        stt._is_loaded = True
        segment_mock = MagicMock()
        segment_mock.text = lambda: segments_text[0]
        segments = [MagicMock(text=lambda: t) for t in segments_text]
        model = MagicMock()
        model.transcribe.return_value = (segments, None)
        stt._model = model
        return stt

    def test_transcribe_success(self) -> None:
        stt = self._make_stt(["Olá", " mundo"])
        result = stt.transcribe("audio.wav")
        assert result == "Olá mundo"
        stt._model.transcribe.assert_called_once()

    def test_transcribe_loads_model_if_not_loaded(self) -> None:
        stt = SpeechToText()
        with patch.object(stt, "load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([MagicMock(text=lambda: "hi")], None)
            stt._model = mock_model
            stt._is_loaded = True
            result = stt.transcribe("audio.wav")
        mock_load.assert_not_called()
        assert result == "hi"

    def test_transcribe_empty_audio(self) -> None:
        stt = self._make_stt([""])
        result = stt.transcribe("audio.wav")
        assert result == ""

    def test_transcribe_no_model_raises(self) -> None:
        stt = SpeechToText()
        stt._is_loaded = True
        stt._model = None
        with pytest.raises(STTError, match="Modelo STT nao carregado"):
            stt.transcribe("audio.wav")

    def test_transcribe_failure_wraps_error(self) -> None:
        stt = SpeechToText()
        stt._is_loaded = True
        model = MagicMock()
        model.transcribe.side_effect = RuntimeError("fail")
        stt._model = model
        with pytest.raises(STTError, match="Falha ao transcrever audio"):
            stt.transcribe("audio.wav")


class TestSpeechToTextTranscribeFromBytes:
    """Testes de transcicao de audio em memoria."""

    def test_transcribe_from_bytes_success(self) -> None:
        stt = SpeechToText()
        stt._is_loaded = True
        model = MagicMock()
        model.transcribe.return_value = ([MagicMock(text=lambda: "ok")], None)
        stt._model = model
        with patch("jarvis.voice.stt.sf") as mock_sf, patch("jarvis.voice.stt.io") as mock_io:
            mock_sf.read.return_value = (b"audio", 16000)
            result = stt.transcribe_from_bytes(b"audio")
        assert result == "ok"
        mock_sf.read.assert_called_once()

    def test_transcribe_from_bytes_sample_rate_mismatch_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        stt = SpeechToText()
        stt._is_loaded = True
        model = MagicMock()
        model.transcribe.return_value = ([MagicMock(text=lambda: "ok")], None)
        stt._model = model
        with patch("jarvis.voice.stt.sf") as mock_sf, patch("jarvis.voice.stt.io"):
            mock_sf.read.return_value = (b"audio", 22050)
            with caplog.at_level(logging.WARNING, logger="jarvis.voice.stt"):
                stt.transcribe_from_bytes(b"audio")
        assert "Taxa de amostragem diferente" in caplog.text

    def test_transcribe_from_bytes_failure_wraps_error(self) -> None:
        stt = SpeechToText()
        stt._is_loaded = True
        model = MagicMock()
        model.transcribe.side_effect = RuntimeError("fail")
        stt._model = model
        with patch("jarvis.voice.stt.sf") as mock_sf, patch("jarvis.voice.stt.io"):
            mock_sf.read.return_value = (b"audio", 16000)
            with pytest.raises(STTError, match="Falha ao transcrever audio de bytes"):
                stt.transcribe_from_bytes(b"audio")