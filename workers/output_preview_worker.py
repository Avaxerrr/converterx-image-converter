"""
Output Preview Worker

Async worker for generating output previews in a background thread.
Prevents UI freezing during image processing.

This worker:
1. Calls OutputPreviewGenerator to generate PIL Image
2. Converts PIL Image → QPixmap for display
3. Emits signals on success/error
"""

from PySide6.QtCore import QObject, QRunnable, Signal, Slot
from PySide6.QtGui import QPixmap, QImage
from PIL import Image
from pathlib import Path
from typing import Optional
import io

from core.output_preview_generator import OutputPreviewGenerator
from core.format_settings import ConversionSettings
from utils.logger import logger, LogLevel


class OutputPreviewSignals(QObject):
    """Signals for output preview worker."""

    # Emits QPixmap when generation succeeds
    finished = Signal(QPixmap, int)

    # Emits error message string when generation fails
    error = Signal(str)


class OutputPreviewWorker(QRunnable):
    """
    Generate output preview in a background thread.

    This worker runs asynchronously in QThreadPool to prevent UI freezing.
    """

    def __init__(
            self,
            image_path: Path,
            settings: ConversionSettings
    ):
        """
        Initialize the output preview worker.

        Args:
            image_path: Path to the source image file
            settings: Conversion settings to apply
        """
        super().__init__()
        self.image_path = image_path
        self.settings = settings
        self.signals = OutputPreviewSignals()

        logger.debug(
            f"OutputPreviewWorker created for {image_path.name}",
            source="OutputPreviewWorker"
        )

    @Slot()
    def run(self):
        """Execute preview generation in worker thread."""
        logger.info(
            f"Worker thread started for {self.image_path.name}",
            source="OutputPreviewWorker"
        )

        try:
            # Step 1: Generate the preview PIL Image
            pil_image = OutputPreviewGenerator.generate_preview(
                self.image_path,
                self.settings
            )

            if pil_image is None:
                error_msg = f"Preview generation returned None for {self.image_path.name}"
                logger.error(error_msg, source="OutputPreviewWorker")
                self.signals.error.emit(error_msg)
                return

            logger.debug(
                f"PIL Image generated: {pil_image.size[0]}×{pil_image.size[1]} (mode={pil_image.mode})",
                source="OutputPreviewWorker"
            )

            # Step 2: Convert to QPixmap with compression and get file size
            pixmap, file_size_bytes = self.pil_to_qpixmap_with_compression(pil_image, self.settings)

            if pixmap.isNull():
                error_msg = f"Failed to convert PIL Image to QPixmap for {self.image_path.name}"
                logger.error(error_msg, source="OutputPreviewWorker")
                self.signals.error.emit(error_msg)
                return

            logger.success(
                f"QPixmap created: {pixmap.width()}×{pixmap.height()}, estimated size: {file_size_bytes / 1024:.2f} KB",
                source="OutputPreviewWorker"
            )

            # Step 3: Emit success signal with pixmap AND file size
            self.signals.finished.emit(pixmap, file_size_bytes)
            logger.info(
                f"Worker completed successfully for {self.image_path.name}",
                source="OutputPreviewWorker"
            )

        except Exception as e:
            error_msg = f"Worker error for {self.image_path.name}: {str(e)}"
            logger.error(error_msg, source="OutputPreviewWorker")
            self.signals.error.emit(error_msg)

    def pil_to_qpixmap_with_compression(self, pil_image: Image.Image, settings: ConversionSettings) -> tuple[
        QPixmap, int]:
        """
        Convert PIL Image to QPixmap WITH compression/quality applied.

        This simulates the compression by saving to an in-memory buffer with the actual
        quality/compression settings, then loading back. This gives a more accurate
        preview of what the exported image will look like.

        Args:
            pil_image: PIL Image to convert
            settings: Settings containing quality/compression info

        Returns:
            Tuple of (QPixmap for display, file_size_bytes)
        """
        try:
            # Get preview-specific save kwargs (quality, compression, lossless)
            save_kwargs = OutputPreviewGenerator.get_preview_kwargs(settings)
            logger.debug(
                f"Applying compression with kwargs: {save_kwargs}",
                source="OutputPreviewWorker"
            )

            # Save to in-memory buffer with compression
            buffer = io.BytesIO()
            pil_image.save(buffer, **save_kwargs)
            buffer.seek(0)

            # Get file size from buffer
            file_size_bytes = len(buffer.getvalue())
            logger.info(
                f"Estimated output size: {file_size_bytes / 1024:.2f} KB",
                source="OutputPreviewWorker"
            )

            # Load back from buffer (now with compression applied)
            compressed_image = Image.open(buffer)

            # Convert to RGB for QImage (simplest/most compatible)
            if compressed_image.mode not in ("RGB", "RGBA"):
                compressed_image = compressed_image.convert("RGB")
                logger.debug(
                    f"Converted to RGB for QImage display",
                    source="OutputPreviewWorker"
                )

            # Convert to QImage
            if compressed_image.mode == "RGB":
                qimage = self._pil_rgb_to_qimage(compressed_image)
            elif compressed_image.mode == "RGBA":
                qimage = self._pil_rgba_to_qimage(compressed_image)
            else:
                # Fallback: convert to RGB
                compressed_image = compressed_image.convert("RGB")
                qimage = self._pil_rgb_to_qimage(compressed_image)

            # Convert QImage to QPixmap
            pixmap = QPixmap.fromImage(qimage)
            logger.debug(
                f"Conversion complete: PIL (compressed) → QPixmap ({pixmap.width()}×{pixmap.height()})",
                source="OutputPreviewWorker"
            )

            return (pixmap, file_size_bytes)  # MODIFIED: Return tuple

        except Exception as e:
            logger.error(
                f"Compression conversion failed: {str(e)}",
                source="OutputPreviewWorker"
            )
            # Fallback: direct conversion without compression
            return (self._pil_to_qpixmap_direct(pil_image), 0)

    @staticmethod
    def _pil_rgb_to_qimage(pil_image: Image.Image) -> QImage:
        """Convert PIL RGB Image to QImage."""
        data = pil_image.tobytes('raw', 'RGB')
        qimage = QImage(
            data,
            pil_image.width,
            pil_image.height,
            pil_image.width * 3,  # bytes per line (3 bytes per RGB pixel)
            QImage.Format.Format_RGB888
        )
        return qimage.copy()  # Copy to detach from original data

    @staticmethod
    def _pil_rgba_to_qimage(pil_image: Image.Image) -> QImage:
        """Convert PIL RGBA Image to QImage."""
        data = pil_image.tobytes('raw', 'RGBA')
        qimage = QImage(
            data,
            pil_image.width,
            pil_image.height,
            pil_image.width * 4,  # bytes per line (4 bytes per RGBA pixel)
            QImage.Format.Format_RGBA8888
        )
        return qimage.copy()  # Copy to detach from original data

    @staticmethod
    def _pil_to_qpixmap_direct(pil_image: Image.Image) -> QPixmap:
        """
        Fallback: Direct conversion without compression.
        Used if compression simulation fails.
        """
        logger.warning(
            "Using direct conversion (no compression applied)",
            source="OutputPreviewWorker"
        )

        # Convert to RGB if needed
        if pil_image.mode not in ('RGB', 'RGBA'):
            pil_image = pil_image.convert('RGB')

        # Convert to QImage
        if pil_image.mode == 'RGB':
            data = pil_image.tobytes('raw', 'RGB')
            qimage = QImage(
                data,
                pil_image.width,
                pil_image.height,
                pil_image.width * 3,
                QImage.Format.Format_RGB888
            )
        else:  # RGBA
            data = pil_image.tobytes('raw', 'RGBA')
            qimage = QImage(
                data,
                pil_image.width,
                pil_image.height,
                pil_image.width * 4,
                QImage.Format.Format_RGBA8888
            )

        return QPixmap.fromImage(qimage.copy())
