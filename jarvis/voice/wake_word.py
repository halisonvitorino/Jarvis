"""
Wake Word detection module for J.A.R.V.I.S.

Detecta palavras-chave para ativar o assistente por voz.
Suporta deteccao simples de palavras-chave via STT.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Palavras-chave configuraveis
- Tratamento de erros explícito com WakeWordError
- Logging ativo em todas as operações
"""

from __future__ import annotations

import logging
from typing import Callable, List, Optional

from .stt import SpeechToText, STTError

logger = logging.getLogger(__name__)


class WakeWordError(Exception):
    """Erro específico do modulo de Wake Word."""


class WakeWordDetector:
    """Detecta palavras-chave para ativar o assistente por voz."""

    def __init__(
        self,
        wake_words: Optional[List[str]] = None,
        stt: Optional[SpeechToText] = None,
        sensitivity: float = 0.8,
    ) -> None:
        """
        Inicializa o detector de palavra-chave.

        Args:
            wake_words: Lista de palavras que ativam o assistente
                (ex: ["jarvis", "hermes"]). Padrao: ["jarvis"].
            stt: Instancia de SpeechToText para deteccao.
            sensitivity: Limiar de confianca para deteccao (0.0 a 1.0).
        """
        self.wake_words = wake_words or ["jarvis"]
        self.sensitivity = sensitivity
        self.stt = stt or SpeechToText()
        self._callback: Optional[Callable[[str], None]] = None
        self._is_listening = False
        logger.info("WakeWordDetector inicializado: palavras=%s", self.wake_words)

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """
        Define a funcao chamada quando uma palavra-chave e detectada.

        Args:
            callback: Funcao a ser executada com o texto transcrito como argumento.
        """
        self._callback = callback
        logger.debug("Callback de wake word definido")

    def start_listening(self) -> None:
        """Inicia a escuta continua para palavra-chave."""
        if self._callback is None:
            raise WakeWordError("Callback nao definido. Use set_callback primeiro.")

        self._is_listening = True
        logger.info("Escuta de wake word iniciada: %s", self.wake_words)

    def stop_listening(self) -> None:
        """Para a escuta de palavra-chave."""
        self._is_listening = False
        logger.debug("Escuta de wake word parada")

    def check_wake_word(self, text: str) -> bool:
        """
        Verifica se um texto contem uma palavra-chave.

        Args:
            text: Texto transcrito para verificar.

        Returns:
            True se alguma palavra-chave foi detectada, False caso contrario.
        """
        if not text or not self._is_listening:
            return False

        text_lower = text.lower().strip()
        for wake_word in self.wake_words:
            if wake_word.lower() in text_lower:
                logger.info("Wake word detectada: '%s' no texto: '%s'", wake_word, text)
                if self._callback:
                    self._callback(text)
                return True
        return False

    def process_audio(self, audio_path: str) -> Optional[str]:
        """
        Processa um arquivo de audio e verifica se contem wake word.

        Args:
            audio_path: Caminho para o arquivo de audio.

        Returns:
            Texto transcrito se wake word foi detectada, None caso contrario.

        Raises:
            WakeWordError: Se falhar o processamento de audio.
        """
        if not self.stt:
            raise WakeWordError("Motor STT nao disponivel para deteccao de wake word")

        try:
            text = self.stt.transcribe(audio_path)
            if self.check_wake_word(text):
                return text
            return None
        except STTError as exc:
            logger.error("Falha STT durante deteccao de wake word: %s", exc)
            raise WakeWordError(f"Falha ao processar audio para wake word: {exc}") from exc