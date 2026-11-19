"""
J.A.R.V.I.S Vision System - Phase 4

Modulo de visão para captura de tela, OCR e leitura de imagens.
Supports screenshot capture, text extraction via EasyOCR, and image analysis.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Modular: cada responsabilidade tem sua classe
- Testável: métodos puros com entradas/saídas explícitas
- Logado: todas as operações críticas têm logging
- Substituível: motores de OCR podem ser trocados sem alterar o core
"""

from .screenshot import ScreenshotError, ScreenCapture
from .ocr import EasyOCRProcessor, OCRProcessingError, OCRResult
from .image_reader import ImageReadError, ImageReader, ImageMetadata, ImageSource

__all__ = [
    "ScreenCapture",
    "EasyOCRProcessor",
    "OCRProcessingError",
    "OCRResult",
    "ImageReader",
    "ImageMetadata",
    "ImageSource",
    "ScreenshotError",
]