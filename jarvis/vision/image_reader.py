"""
Image reading and basic analysis module for J.A.R.V.I.S.

Provides functionality to read images from various sources and perform
basic analysis such as format detection, size, and mode information.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Tratamento de erros explícito com ImageReadError
- Logging ativo em todas as operações
- Interface consistente com o módulo OCR
"""


from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ImageReadError(Exception):
    """Erro específico do modulo de leitura de imagem."""


class ImageReader:
    """Lê e fornece metadados básicos de imagens usando PIL/Pillow.

    Responsibilities:
    - Open images from file paths or bytes
    - Return format, size, and color mode
    - Convert between different image formats
    - Provide thumbnail generation support
    """

    def __init__(self) -> None:
        """Inicializa o leitor de imagem."""
        logger.info("ImageReader initialized")

    def read_from_path(self, image_path: str) -> "ImageMetadata":
        """Read an image from a file path.

        Args:
            image_path: Path to the image file.

        Returns:
            ImageMetadata with image information.

        Raises:
            ImageReadError: If the image cannot be read.
        """
        try:
            from PIL import Image

            image_path = Path(image_path)
            if not image_path.exists():
                raise ImageReadError(f"Image file not found: {image_path}")

            with Image.open(image_path) as img:
                # Ensure image is loaded
                img.load()

                metadata = ImageMetadata(
                    path=str(image_path.resolve()),
                    format=img.format,
                    width=img.width,
                    height=img.height,
                    mode=img.mode,
                    size=img.size,
                    is_animated=getattr(img, "is_animated", False),
                )
                logger.debug(
                    "Image read from %s: %s %dx%d mode=%s",
                    image_path,
                    metadata.format,
                    metadata.width,
                    metadata.height,
                    metadata.mode,
                )
                return metadata

        except ImageReadError:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to read image from %s: %s", image_path, exc)
            raise ImageReadError(f"Falha ao ler imagem de {image_path}: {exc}") from exc

    def read_from_bytes(self, image_bytes: bytes) -> "ImageMetadata":
        """Read an image from raw bytes.

        Args:
            image_bytes: Raw image bytes (PNG, JPEG, etc.).

        Returns:
            ImageMetadata with image information.

        Raises:
            ImageReadError: If the image cannot be read.
        """
        try:
            from PIL import Image
            import io

            image_bytes_io = io.BytesIO(image_bytes)
            with Image.open(image_bytes_io) as img:
                # Ensure image is loaded
                img.load()

                metadata = ImageMetadata(
                    path="bytes_input",
                    format=img.format,
                    width=img.width,
                    height=img.height,
                    mode=img.mode,
                    size=img.size,
                    is_animated=getattr(img, "is_animated", False),
                )
                logger.debug(
                    "Image read from bytes: %s %dx%d mode=%s",
                    metadata.format,
                    metadata.width,
                    metadata.height,
                    metadata.mode,
                )
                return metadata

        except ImageReadError:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to read image from bytes: %s", exc)
            raise ImageReadError(f"Falha ao ler imagem de bytes: {exc}") from exc

    @staticmethod
    def get_format_name(format_value: Optional[str]) -> str:
        """Get a human-readable format name.

        Args:
            format_value: The format code from PIL (e.g., 'PNG', 'JPEG').

        Returns:
            Human-readable format name.
        """
        if format_value is None:
            return "Unknown"
        return format_value.upper()


class ImageSource:
    """Generic image source abstraction for image reading.

    Accepts either a file path or raw bytes as the image source.
    """

    def __init__(self, path: str = None, bytes_data: bytes = None) -> None:
        """Inicializa a fonte de imagem.

        Args:
            path: File path to the image.
            bytes_data: Raw image bytes.
        """
        self.path = path
        self.bytes = bytes_data


@dataclass
class ImageMetadata:
    """Metadata structure for image information."""

    path: str
    format: str
    width: int
    height: int
    mode: str
    size: Tuple[int, int]
    is_animated: bool = False