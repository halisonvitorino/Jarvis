"""
Text-to-Speech (TTS) module for J.A.R.V.I.S.

Uses Piper TTS for offline speech synthesis.
Converts text into spoken audio.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Tratamento de erros explícito com TTSError
- Logging ativo em todas as operações
- Voz configuravel
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TTSError(Exception):
    """Erro específico do modulo Text-to-Speech."""


class TextToSpeech:
    """Sintetiza texto em fala usando Piper TTS (offline)."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        output_dir: str = "data/voice/output",
    ) -> None:
        """
        Inicializa o motor de TTS.

        Args:
            model_path: Caminho para o modelo de voz Piper (.onnx).
            config_path: Caminho para o arquivo de configuracao do modelo (.json).
            output_dir: Diretorio para salvar arquivos de audio gerados.
        """
        self.model_path = model_path
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._engine = None
        self._is_loaded = False
        logger.info("TextToSpeech inicializado: saida=%s", self.output_dir)

    def load_model(self) -> None:
        """Carrega o modelo de voz Piper na memoria."""
        if self._is_loaded:
            logger.debug("Modelo TTS ja carregado")
            return

        try:
            from piper import PiperVoice  # type: ignore

            self._engine = PiperVoice.load(
                model_path=self.model_path,
                config_path=self.config_path,
            )
            self._is_loaded = True
            logger.info("Modelo TTS carregado com sucesso")
        except ImportError as exc:
            logger.error("piper-tts nao instalado: %s", exc)
            raise TTSError(f"piper-tts nao disponivel: {exc}") from exc
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Falha ao carregar modelo TTS: %s", exc)
            raise TTSError(f"Nao foi possivel carregar o modelo TTS: {exc}") from exc

    def synthesize(self, text: str, output_file: Optional[str] = None) -> str:
        """
        Sintetiza texto em arquivo de audio.

        Args:
            text: Texto para ser convertido em fala.
            output_file: Caminho para salvar o arquivo de audio. Se None, gera nome automatico.

        Returns:
            Caminho para o arquivo de audio gerado.

        Raises:
            TTSError: Se o modelo nao estiver carregado ou falhar a sintese.
        """
        if not self._is_loaded:
            self.load_model()

        if self._engine is None:
            raise TTSError("Modelo TTS nao carregado")

        if not text or not text.strip():
            raise TTSError("Texto vazio nao pode ser sintetizado")

        if output_file is None:
            import hashlib

            text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
            output_file = str(self.output_dir / f"tts_{text_hash}.wav")

        import wave
        try:
            with wave.open(str(output_file), "wb") as wav_file:
                self._engine.synthesize_wav(text, wav_file, set_wav_format=True)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Falha na sintese TTS: %s", exc)
            raise TTSError(f"Falha ao sintetizar texto: {exc}") from exc
        logger.debug("Sintese TTS concluida: %s -> %s", text[:50], output_file)
        return output_file

    def synthesize_and_play(self, text: str) -> None:
        """
        Sintetiza texto e reproduz o audio imediatamente.

        Args:
            text: Texto para ser convertido em fala e reproduzido.

        Raises:
            TTSError: Se falhar a sintese ou reproducao.
        """
        try:
            import sounddevice as sd  # type: ignore
            import soundfile as sf  # type: ignore

            output_file = self.synthesize(text)
            audio_data, sample_rate = sf.read(output_file)
            sd.play(audio_data, sample_rate)
            sd.wait()
            logger.debug("Reproducao TTS concluida: %s", text[:50])
        except ImportError as exc:
            logger.error("sounddevice ou soundfile nao instalado: %s", exc)
            raise TTSError(f"sounddevice ou soundfile nao disponivel: {exc}") from exc
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Falha na reproducao TTS: %s", exc)
            raise TTSError(f"Falha ao reproduzir fala: {exc}") from exc