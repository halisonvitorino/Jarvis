"""
Speech-to-Text (STT) module for J.A.R.V.I.S.

Uses faster-whisper for offline speech recognition.
Converts audio input from microphone into text.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Tratamento de erros explícito com STTError
- Logging ativo em todas as operações
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class STTError(Exception):
    """Erro específico do modulo Speech-to-Text."""


class SpeechToText:
    """Transcreve fala em texto usando faster-whisper (offline)."""

    def __init__(
        self,
        model_size: str = "base",
        language: Optional[str] = None,
        compute_type: str = "int8",
    ) -> None:
        """
        Inicializa o motor de STT.

        Args:
            model_size: Tamanho do modelo Whisper (tiny, base, small, medium, large-v3).
            language: Codigo do idioma (ex: 'pt', 'en'). None = deteccao automatica.
            compute_type: Tipo de computacao (int8 para CPU mais rapida, float16 para GPU).
        """
        self.model_size = model_size
        self.language = language
        self.compute_type = compute_type
        self._model = None
        self._is_loaded = False
        logger.info("SpeechToText inicializado: modelo=%s, idioma=%s", model_size, language or "auto")

    def load_model(self) -> None:
        """Carrega o modelo Whisper na memoria."""
        if self._is_loaded:
            logger.debug("Modelo STT ja carregado")
            return

        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                compute_type=self.compute_type,
            )
            self._is_loaded = True
            logger.info("Modelo STT carregado com sucesso: %s", self.model_size)
        except ImportError as exc:
            logger.error("faster-whisper nao instalado: %s", exc)
            raise STTError(f"faster-whisper nao disponivel: {exc}") from exc
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Falha ao carregar modelo STT: %s", exc)
            raise STTError(f"Nao foi possivel carregar o modelo STT: {exc}") from exc

    def transcribe(self, audio_path: str) -> str:
        """
        Transcreve um arquivo de audio em texto.

        Args:
            audio_path: Caminho para o arquivo de audio (.wav, .mp3, etc).

        Returns:
            Texto transcrito do audio.

        Raises:
            STTError: Se o modelo nao estiver carregado ou falhar a transcricao.
        """
        if not self._is_loaded:
            self.load_model()

        if self._model is None:
            raise STTError("Modelo STT nao carregado")

        try:
            segments, _ = self._model.transcribe(
                audio_path,
                language=self.language,
                vad_filter=True,
            )
            text = " ".join(segment.text for segment in segments)
            logger.debug("Transcricao concluida: %s", text[:100] if text else "")
            return text.strip()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Falha na transcricao STT: %s", exc)
            raise STTError(f"Falha ao transcrever audio: {exc}") from exc

    def transcribe_from_bytes(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """
        Transcreve audio de bytes em memoria.

        Args:
            audio_bytes: Dados de audio em formato WAV.
            sample_rate: Taxa de amostragem do audio.

        Returns:
            Texto transcrito do audio.

        Raises:
            STTError: Se falhar a transcricao.
        """
        import io
        import soundfile as sf  # type: ignore

        if not self._is_loaded:
            self.load_model()

        if self._model is None:
            raise STTError("Modelo STT nao carregado")

        try:
            audio_buffer = io.BytesIO(audio_bytes)
            audio_data, sr = sf.read(audio_buffer)
            if sr != sample_rate:
                logger.warning("Taxa de amostragem diferente: esperado %d, recebido %d", sample_rate, sr)

            segments, _ = self._model.transcribe(
                audio_data,
                language=self.language,
                vad_filter=True,
            )
            text = " ".join(segment.text for segment in segments)
            logger.debug("Transcricao de bytes concluida: %s", text[:100] if text else "")
            return text.strip()
        except ImportError as exc:
            logger.error("soundfile nao instalado: %s", exc)
            raise STTError(f"soundfile nao disponivel: {exc}") from exc
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Falha na transcricao de bytes STT: %s", exc)
            raise STTError(f"Falha ao transcrever audio de bytes: {exc}") from exc