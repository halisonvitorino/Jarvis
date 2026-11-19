"""
Screenshot capture module for J.A.R.V.I.S.

Uses mss (Multi-Screen Shot Tool) for fast screen capture.
Supports full screen, specific monitor, and specific window capture.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Tratamento de erros explícito com ScreenshotError
- Logging ativo em todas as operações
- Captura otimizada para processamento posterior
"""


import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class ScreenshotError(Exception):
    """Erro específico do modulo de captura de tela."""


class ScreenCapture:
    """Captura de tela usando mss para desempenho otimizado."""

    def __init__(self, monitor_index: int = 1) -> None:
        """Inicializa o capturador de tela.

        Args:
            monitor_index: Índice do monitor para captura (1 = primary).
                           Use 0 para tela inteira (todos os monitores).
        """
        self.monitor_index = monitor_index
        self._mss = None
        logger.info("ScreenCapture inicializado: monitor_index=%s", monitor_index)

    @property
    def mss(self):
        """Lazy import mss to avoid heavy import at startup."""
        if self._mss is None:
            import mss

            self._mss = mss
        return self._mss

    def capture_full(self) -> bytes:
        """Capture the full screen (all monitors combined).

        Returns:
            Raw bytes of the screenshot in PNG format.

        Raises:
            ScreenshotError: If capture fails.
        """
        try:
            screenshot = self.mss.grab(self._get_monitor())
            import mss.tools

            # Convert to PNG bytes
            png_bytes = mss.tools.to_png(
                screenshot.rgb,
                screenshot.size,
            )
            logger.debug("Full screen capture successful: %dx%d", *screenshot.size)
            return png_bytes
        except Exception as exc:
            logger.error("Failed to capture full screen: %s", exc)
            raise ScreenshotError(f"Falha ao capturar tela completa: {exc}") from exc

    def capture_monitor(self, monitor_index: Optional[int] = None) -> bytes:
        """Capture a specific monitor.

        Args:
            monitor_index: Index of the monitor to capture. Uses initialized
                           monitor_index if not specified.

        Returns:
            Raw bytes of the screenshot in PNG format.

        Raises:
            ScreenshotError: If capture fails.
        """
        idx = monitor_index if monitor_index is not None else self.monitor_index
        try:
            screenshot = self.mss.grab(self.mss.monitors[idx])
            import mss.tools

            png_bytes = mss.tools.to_png(
                screenshot.rgb,
                screenshot.size,
            )
            logger.debug("Monitor %d capture successful: %dx%d", idx, *screenshot.size)
            return png_bytes
        except Exception as exc:
            logger.error("Failed to capture monitor %d: %s", idx, exc)
            raise ScreenshotError(f"Falha ao capturar monitor {idx}: {exc}") from exc

    def capture_region(
        self, x: int, y: int, width: int, height: int
    ) -> bytes:
        """Capture a specific screen region.

        Args:
            x: Left coordinate of the region.
            y: Top coordinate of the region.
            width: Width of the region.
            height: Height of the region.

        Returns:
            Raw bytes of the screenshot in PNG format.

        Raises:
            ScreenshotError: If capture fails.
        """
        try:
            # mss monitor format: {left, top, width, height}
            monitor = {"left": x, "top": y, "width": width, "height": height}
            screenshot = self.mss.grab(monitor)
            import mss.tools

            png_bytes = mss.tools.to_png(
                screenshot.rgb,
                screenshot.size,
            )
            logger.debug("Region capture [%d,%d,%d,%d] successful: %dx%d",
                        x, y, width, height, *screenshot.size)
            return png_bytes
        except Exception as exc:
            logger.error("Failed to capture region [%d,%d,%d,%d]: %s", x, y, width, height, exc)
            raise ScreenshotError(f"Falha ao capturar região [{x},{y},{width},{height}]: {exc}") from exc

    def _get_monitor(self) -> Dict[str, int]:
        """Get the monitor dictionary for the configured monitor index."""
        monitors = self.mss.monitors
        if self.monitor_index < len(monitors):
            return monitors[self.monitor_index]
        # Fall back to primary monitor (index 1)
        logger.warning("Monitor index %d out of range, using primary (1)", self.monitor_index)
        return monitors[1]

    def save_screenshot(self, filepath: str, monitor_index: Optional[int] = None) -> str:
        """Capture and save screenshot to file.

        Args:
            filepath: Path where the screenshot will be saved.
            monitor_index: Optional monitor index to capture.

        Returns:
            The filepath where the screenshot was saved.

        Raises:
            ScreenshotError: If capture or save fails.
        """
        import mss.tools

        try:
            png_bytes = self.capture_monitor(monitor_index)
            with open(filepath, "wb") as f:
                f.write(png_bytes)
            logger.info("Screenshot saved to: %s", filepath)
            return filepath
        except Exception as exc:
            logger.error("Failed to save screenshot to %s: %s", filepath, exc)
            raise ScreenshotError(f"Falha ao salvar screenshot em {filepath}: {exc}") from exc