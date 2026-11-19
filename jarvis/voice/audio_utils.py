"""
Audio utilities module for J.A.R.V.I.S.

Funcoes utilitarias para processamento de audio.
Suporta gravacao de microfone e conversão de formatos.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Tratamento de erros explícito com AudioUtilsError
- Logging ativo em todas as operações
- Modular: funcoes independentes e testaveis
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AudioUtilsError(Exception):
    """Erro específico do modulo de utilitarios de audio."""


def record_audio(
    output_path: str,
    duration: float = 5.0,
    sample_rate: int = 16000,
) -> str:
    """
    Gera audio do microfone por um periodo determinado.

    Args:
        output_path: Caminho para salvar o arquivo de audio gravado.
        duration: Duracao da gravacao em segundos.
        sample_rate: Taxa de amostragem em Hz.

    Returns:
        Caminho para o arquivo de audio gravado.

    Raises:
        AudioUtilsError: Se falhar a gravacao.
    """
    try:
        import sounddevice as sd  # type: ignore
        import soundfile as sf  # type: ignore

        logger.info("Gravando audio por %.1f segundos em %s", duration, output_path)
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()
        sf.write(output_path, audio_data, sample_rate)
        logger.debug("Gravacao concluida: %s", output_path)
        return output_path
    except ImportError as exc:
        logger.error("sounddevice ou soundfile nao instalado: %s", exc)
        raise AudioUtilsError(f"sounddevice ou soundfile nao disponivel: {exc}") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Falha na gravacao de audio: %s", exc)
        raise AudioUtilsError(f"Falha ao gravar audio: {exc}") from exc


def convert_audio_format(
    input_path: str,
    output_path: str,
    target_format: str = "wav",
) -> str:
    """
    Converte arquivo de audio para outro formato.

    Args:
        input_path: Caminho para o arquivo de entrada.
        output_path: Caminho para o arquivo de saida.
        target_format: Formato de saida (ex: 'wav', 'mp3').

    Returns:
        Caminho para o arquivo de saida convertido.

    Raises:
        AudioUtilsError: Se falhar a conversão.
    """
    try:
        from pydub import AudioSegment  # type: ignore

        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format=target_format)
        logger.debug("Conversão de audio concluida: %s -> %s (%s)", input_path, output_path, target_format)
        return output_path
    except ImportError as exc:
        logger.error("pydub nao instalado: %s", exc)
        raise AudioUtilsError(f"pydub nao disponivel: {exc}") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Falha na conversão de audio: %s", exc)
        raise AudioUtilsError(f"Falha ao converter audio: {exc}") from exc


def validate_audio_file(file_path: str) -> bool:
    """
    Valida se um arquivo de audio existe e eh valido.

    Args:
        file_path: Caminho para o arquivo de audio.

    Returns:
        True se o arquivo existe e eh valido, False caso contrario.
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning("Arquivo de audio nao encontrado: %s", file_path)
        return False

    valid_extensions = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
    if path.suffix.lower() not in valid_extensions:
        logger.warning("Formato de audio nao suportado: %s", path.suffix)
        return False

    logger.debug("Arquivo de audio valido: %s", file_path)
    return True


def list_audio_devices() -> dict:
    """
    Lista dispositivos de audio disponíveis (entrada e saída).

    Returns:
        Dicionario com dispositivos de entrada e saída.

    Raises:
        AudioUtilsError: Se falhar a listagem de dispositivos.
    """
    try:
        import sounddevice as sd  # type: ignore

        devices = sd.query_devices()
        input_devices = []
        output_devices = []

        for i, device in enumerate(devices):
            device_info = {
                "index": i,
                "name": device["name"],
                "channels": device["max_input_channels"] if device["max_input_channels"] > 0 else device["max_output_channels"],
                "sample_rate": device["default_samplerate"],
            }
            if device["max_input_channels"] > 0:
                input_devices.append(device_info)
            if device["max_output_channels"] > 0:
                output_devices.append(device_info)

        logger.debug("Dispositivos de audio listados: %d entrada, %d saida", len(input_devices), len(output_devices))
        return {
            "input": input_devices,
            "output": output_devices,
        }
    except ImportError as exc:
        logger.error("sounddevice nao instalado: %s", exc)
        raise AudioUtilsError(f"sounddevice nao disponivel: {exc}") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Falha ao listar dispositivos de audio: %s", exc)
        raise AudioUtilsError(f"Falha ao listar dispositivos: {exc}") from exc