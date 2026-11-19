"""
OCR processing module for J.A.R.V.I.S.

Uses EasyOCR for text extraction from images.
Supports single-language and multi-language OCR with automatic language detection.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Tratamento de erros explícito com OCRProcessingError
- Logging ativo em todas as operações
- Processamento otimizado para uso em assistente pessoal
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class OCRProcessingError(Exception):
    """Erro específico do modulo de processamento OCR."""


@dataclass
class OCRResult:
    """Result structure from OCR processing."""

    text: str
    lines: List[dict]
    average_confidence: float
    num_detections: int


class EasyOCRProcessor:
    """Processador de O usando EasyOCR para extração de texto de imagens.

    Responsibilities:
    - Initialize EasyOCR reader (can be slow, cached after init)
    - Extract text from image bytes or file paths
    - Support multiple languages
    - Return structured results with bounding boxes and confidence
    """

    def __init__(
        self,
        languages: List[str] = None,
        use_gpu: bool = False,
        gpu_memory_fraction: float = 0.5,
    ) -> None:
        """Inicializa o processador EasyOCR.

        Args:
            languages: List of language codes (ex: ['en'], ['pt'], ['en', 'pt']).
                       None = default to English.
            use_gpu: Whether to use GPU for OCR processing.
            gpu_memory_fraction: Fraction of GPU memory to use (if GPU enabled).

        Princípios ASD-STE100:
        - Initialize once, reuse for multiple captures (Eficiência de recursos)
        - Nomes de parâmetros descriptivos em inglês
        - Logging de todas as operações críticas
        """
        if languages is None:
            languages = ["en"]
        self.languages = languages
        self.use_gpu = use_gpu
        self.gpu_memory_fraction = gpu_memory_fraction
        self._reader = None
        self._initialized = False
        logger.info(
            "EasyOCRProcessor configurado: idiomas=%s, GPU=%s",
            languages,
            use_gpu,
        )

    def load_model(self) -> None:
        """Load the EasyOCR model.

        Must be called before OCR processing. The model is cached after first load.

        Raises:
            OCRProcessingError: If EasyOCR is not available or model fails to load.
        """
        if self._initialized:
            logger.debug("EasyOCR model already loaded")
            return

        try:
            from easyocr import Reader

            self._reader = Reader(
                self.languages,
                gpu=self.use_gpu,
                gpu_memory_fraction=self.gpu_memory_fraction,
            )
            self._initialized = True
            logger.info(
                "EasyOCR model loaded successfully: languages=%s, GPU=%s",
                self.languages,
                self.use_gpu,
            )
        except ImportError as exc:
            logger.error("EasyOCR not installed: %s", exc)
            raise OCRProcessingError(
                f"EasyOCR não disponível: {exc}"
            ) from exc
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to load EasyOCR model: %s", exc)
            raise OCRProcessingError(
                f"Não foi possível carregar o modelo EasyOCR: {exc}"
            ) from exc

    def extract_text(self, image_source: "ImageSource") -> OCRResult:
        """Extract text from an image.

        Args:
            image_source: ImageSource object (file path or bytes).

        Returns:
            OCRResult with extracted text and metadata.

        Raises:
            OCRProcessingError: If image cannot be processed or OCR fails.
        """
        if not self._initialized:
            self.load_model()

        if self._reader is None:
            raise OCRProcessingError("EasyOCR reader not initialized")

        try:
            # Get the image as bytes or path
            if hasattr(image_source, "path"):
                # File path
                result = self._reader.readtext(image_source.path)
            elif hasattr(image_source, "bytes"):
                # Bytes - write to temp file for EasyOCR
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as tmp:
                    tmp.write(image_source.bytes)
                    tmp_path = tmp.name
                try:
                    result = self._reader.readtext(tmp_path)
                finally:
                    os.unlink(tmp_path)
            else:
                raise OCRProcessingError(
                    "ImageSource must have 'path' or 'bytes' attribute"
                )

            # Process results into structured format
            text_lines = []
            total_confidence = 0.0
            valid_detections = 0

            for detection in result:
                text = detection[1]
                confidence = detection[2]
                text_lines.append(
                    {"text": text, "confidence": confidence}
                )
                total_confidence += confidence
                valid_detections += 1

            avg_confidence = (
                total_confidence / valid_detections if valid_detections > 0 else 0.0
            )

            logger.debug(
                "OCR extraction completed: %d detections, avg confidence: %.2f",
                valid_detections,
                avg_confidence,
            )

            return OCRResult(
                text=" ".join(line["text"] for line in text_lines if line["text"]),
                lines=text_lines,
                average_confidence=avg_confidence,
                num_detections=valid_detections,
            )

        except Exception as exc:  # pylint: disable=broad-except
            logger.error("OCR processing failed: %s", exc)
            raise OCRProcessingError(f"Falha no processamento OCR: {exc}") from exc

    def extract_text_from_bytes(self, image_bytes: bytes) -> OCRResult:
        """Extract text from image bytes.

        Convenience method that creates a temporary image source from bytes.

        Args:
            image_bytes: Raw image bytes (PNG, JPEG, etc.).

        Returns:
            OCRResult with extracted text and metadata.

        Raises:
            OCRProcessingError: If image cannot be processed or OCR fails.
        """

        class _ImageBytesSource:
            def __init__(self, b: bytes):
                self.bytes = b

        return self.extract_text(_ImageBytesSource(image_bytes))

    def extract_text_from_path(self, image_path: str) -> OCRResult:
        """Extract text from an image file path.

        Convenience method.

        Args:
            image_path: Path to the image file.

        Returns:
            OCRResult with extracted text and metadata.

        Raises:
            OCRProcessingError: If image cannot be processed or OCR fails.
        """

        class _ImagePathSource:
            def __init__(self, p: str):
                self.path = p

        return self.extract_text(_ImagePathSource(image_path))


class ImageSource:
    """Generic image source abstraction for OCR processing.

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