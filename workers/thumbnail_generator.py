"""
Thumbnail generator worker for async thumbnail creation.
"""

from PySide6.QtCore import QObject, Signal, QRunnable
from PySide6.QtGui import QPixmap, QImage
from PIL import Image, ImageOps
from pathlib import Path
from typing import Optional


class ThumbnailSignals(QObject):
    """Signals for thumbnail generation."""
    finished = Signal(int, QPixmap)  # (row_index, thumbnail_pixmap)
    error = Signal(int, str)  # (row_index, error_message)


class ThumbnailGenerator(QRunnable):
    """Generate thumbnails asynchronously."""

    # Configuration
    MAX_HEIGHT = 24
    MIN_WIDTH = 20
    MAX_WIDTH = 80

    def __init__(self, image_path: Path, row_index: int):
        super().__init__()
        self.image_path = image_path
        self.row_index = row_index
        self.signals = ThumbnailSignals()

    def run(self):
        """Generate thumbnail in background thread."""
        try:
            thumbnail = self._generate_thumbnail()
            if thumbnail and not thumbnail.isNull():
                self.signals.finished.emit(self.row_index, thumbnail)
            else:
                self.signals.error.emit(self.row_index, "Failed to generate thumbnail")
        except Exception as e:
            self.signals.error.emit(self.row_index, str(e))

    def _generate_thumbnail(self) -> Optional[QPixmap]:
        """Generate aspect-ratio-preserving thumbnail using PIL."""
        try:
            with Image.open(self.image_path) as img:
                # Apply EXIF orientation
                img = ImageOps.exif_transpose(img)

                # Calculate dimensions maintaining aspect ratio
                aspect_ratio = img.width / img.height
                thumb_height = self.MAX_HEIGHT
                thumb_width = int(self.MAX_HEIGHT * aspect_ratio)

                # Clamp width to reasonable limits
                thumb_width = max(self.MIN_WIDTH, min(thumb_width, self.MAX_WIDTH))

                # Resize image
                img_resized = img.resize(
                    (thumb_width, thumb_height),
                    Image.Resampling.LANCZOS
                )

                # Convert to RGB/RGBA for Qt compatibility
                if img_resized.mode not in ('RGB', 'RGBA'):
                    if img_resized.mode == 'P':
                        img_resized = img_resized.convert('RGBA')
                    else:
                        img_resized = img_resized.convert('RGB')

                # Convert PIL image to QPixmap
                if img_resized.mode == 'RGBA':
                    data = img_resized.tobytes('raw', 'RGBA')
                    qimage = QImage(
                        data,
                        img_resized.width,
                        img_resized.height,
                        img_resized.width * 4,
                        QImage.Format_RGBA8888
                    )
                else:  # RGB
                    data = img_resized.tobytes('raw', 'RGB')
                    qimage = QImage(
                        data,
                        img_resized.width,
                        img_resized.height,
                        img_resized.width * 3,
                        QImage.Format_RGB888
                    )

                return QPixmap.fromImage(qimage)

        except Exception as e:
            print(f"Thumbnail generation failed for {self.image_path.name}: {e}")
            return None
