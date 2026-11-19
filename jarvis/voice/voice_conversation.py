"""
Voice conversation module for J.A.R.V.I.S.

Integra módulos de voz (STT, TTS, wake word) com o ConversationManager existente.
Permite interacao por voz com o assistente.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Integração desacoplada com ConversationManager
- Tratamento de erros explícito com VoiceConversationError
- Logging ativo em todas as operações
- Substituível: pode ser trocado sem alterar o core do sistema
"""

from __future__ import annotations

import logging
from typing import Optional

from jarvis.brain.conversation_manager import ConversationManager
from jarvis.voice.stt import SpeechToText, STTError
from jarvis.voice.tts import TextToSpeech, TTSError
from jarvis.voice.wake_word import WakeWordDetector, WakeWordError

logger = logging.getLogger(__name__)


class VoiceConversationError(Exception):
    """Erro específico do modulo de conversa por voz."""


class VoiceConversation:
    """Gerencia interacao por voz com o J.A.R.V.I.S."""

    def __init__(
        self,
        conversation_manager: ConversationManager,
        stt: Optional[SpeechToText] = None,
        tts: Optional[TextToSpeech] = None,
        wake_word: Optional[WakeWordDetector] = None,
        auto_wake: bool = False,
    ) -> None:
        """
        Inicializa a conversa por voz.

        Args:
            conversation_manager: Instancia do ConversationManager existente.
            stt: Motor de Speech-to-Text.
            tts: Motor de Text-to-Speech.
            wake_word: Detector de palavra-chave.
            auto_wake: Se True, inicia escuta automaticamente.
        """
        self.conversation_manager = conversation_manager
        self.stt = stt or SpeechToText()
        self.tts = tts or TextToSpeech()
        self.wake_word = wake_word or WakeWordDetector(stt=self.stt)
        self.auto_wake = auto_wake
        self._is_active = False
        logger.info("VoiceConversation inicializado: auto_wake=%s", auto_wake)

    def start(self) -> None:
        """Inicia o modo de conversa por voz."""
        try:
            self.stt.load_model()
            self.tts.load_model()
        except (STTError, TTSError) as exc:
            logger.error("Falha ao carregar modelos de voz: %s", exc)
            raise VoiceConversationError(f"Nao foi possível iniciar conversa por voz: {exc}") from exc

        self._is_active = True
        logger.info("Conversa por voz iniciada")

        if self.auto_wake:
            self.wake_word.set_callback(self._on_wake_word)
            self.wake_word.start_listening()

    def stop(self) -> None:
        """Para o modo de conversa por voz."""
        self._is_active = False
        self.wake_word.stop_listening()
        logger.info("Conversa por voz parada")

    def process_voice_input(self, audio_path: str) -> str:
        """
        Processa entrada de voz: transcreve, envia para ConversationManager e sintetiza resposta.

        Args:
            audio_path: Caminho para o arquivo de audio de entrada.

        Returns:
            Resposta sintetizada em texto.

        Raises:
            VoiceConversationError: Se falhar qualquer etapa do processo.
        """
        if not self._is_active:
            raise VoiceConversationError("Conversa por voz nao esta ativa. Use start() primeiro.")

        try:
            # 1. Transcrever audio em texto
            user_text = self.stt.transcribe(audio_path)
            logger.debug("Usuario disse: %s", user_text)

            # 2. Enviar para ConversationManager
            session_id = "voice_session"
            result = self.conversation_manager.chat(
                session_id=session_id,
                message=user_text,
            )
            assistant_text = result.get("response", "")
            logger.debug("JARVIS respondeu: %s", assistant_text[:100] if assistant_text else "")

            # 3. Sintetizar resposta em fala
            self.tts.synthesize_and_play(assistant_text)

            return assistant_text

        except (STTError, TTSError) as exc:
            logger.error("Falha na conversa por voz: %s", exc)
            raise VoiceConversationError(f"Falha no processamento de voz: {exc}") from exc
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Falha inesperada na conversa por voz: %s", exc)
            raise VoiceConversationError(f"Falha inesperada: {exc}") from exc

    def _on_wake_word(self, text: str) -> None:
        """Callback executado quando palavra-chave é detectada."""
        logger.info("Wake word ativada. Aguardando comando...")
        # Aqui seria iniciada a captura de audio para o comando
        # Esta implementacao e base; a captura de audio do microfone
        # depende da configuracao de hardware do usuario