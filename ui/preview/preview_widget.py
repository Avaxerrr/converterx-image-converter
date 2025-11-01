"""
Widget for displaying image preview with zoom and rotation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QGraphicsScene, QGraphicsPixmapItem
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QTransform, QImage
from pathlib import Path
from models.image_file import ImageFile
from ui.metadata_dialog import MetadataDialog
from .image_graphics_view import ImageGraphicsView
from .preview_toolbar import PreviewToolbar


class PreviewWidget(QWidget):
    """Widget for displaying image preview with zoom and rotation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: ImageFile = None
        self.current_pixmap: QPixmap = None
        self.current_rotation: int = 0
        self.original_pixmap: QPixmap = None
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 22)
        layout.setSpacing(6)

        # === ADD HEADER ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Title label
        self.title_label = QLabel("Preview")
        self.title_label.setObjectName("panelHeader")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Graphics view for image display
        self.view = ImageGraphicsView()
        self.view.setObjectName("imageView")

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.pixmap_item = None

        layout.addWidget(self.view, stretch=1)

        # Create floating toolbar (will be positioned over the view)
        self.toolbar = PreviewToolbar(self.view)
        self.toolbar.hide()

        # Connect toolbar signals to internal methods
        self.toolbar.rotate_left_clicked.connect(lambda: self._rotate_image(-90))
        self.toolbar.rotate_right_clicked.connect(lambda: self._rotate_image(90))
        self.toolbar.fit_to_window_clicked.connect(self._fit_to_window)
        self.toolbar.show_metadata_clicked.connect(self._show_metadata)

        # Zoom info label at bottom
        self.zoom_label = QLabel("Use mouse wheel to zoom • Drag to pan")
        self.zoom_label.setObjectName("zoomLabel")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.zoom_label)

    def _position_floating_toolbar(self):
        """Position the floating toolbar in the top-right corner."""
        if hasattr(self, 'toolbar'):
            margin_right = 16
            margin_top = 12
            toolbar_width = self.toolbar.sizeHint().width()
            toolbar_height = self.toolbar.sizeHint().height()

            x = self.view.width() - toolbar_width - margin_right
            y = margin_top

            self.toolbar.move(x, y)
            self.toolbar.raise_()

    def resizeEvent(self, event):
        """Handle widget resize to reposition toolbar."""
        super().resizeEvent(event)
        self._position_floating_toolbar()

    def _load_image_with_exif_fix(self, image_path: Path) -> QPixmap:
        """Load image using PIL (supports AVIF) and convert to QPixmap with EXIF orientation fix."""
        try:
            from PIL import Image, ImageOps

            # Load with PIL (this supports AVIF via pillow-avif-plugin)
            with Image.open(image_path) as pil_image:
                # Apply EXIF orientation
                pil_image = ImageOps.exif_transpose(pil_image)

                # Convert to RGB/RGBA for compatibility
                if pil_image.mode not in ('RGB', 'RGBA'):
                    if pil_image.mode == 'P':  # Palette mode
                        pil_image = pil_image.convert('RGBA')
                    else:
                        pil_image = pil_image.convert('RGB')

                # Convert PIL image to QPixmap
                if pil_image.mode == 'RGBA':
                    data = pil_image.tobytes('raw', 'RGBA')
                    qimage = QImage(
                        data,
                        pil_image.width,
                        pil_image.height,
                        pil_image.width * 4,  # bytes per line
                        QImage.Format_RGBA8888
                    )
                else:  # RGB
                    data = pil_image.tobytes('raw', 'RGB')
                    qimage = QImage(
                        data,
                        pil_image.width,
                        pil_image.height,
                        pil_image.width * 3,  # bytes per line
                        QImage.Format_RGB888
                    )

                return QPixmap.fromImage(qimage)

        except Exception as e:
            print(f"Failed to read image: {e}")
            return QPixmap()  # Return empty pixmap on error

    def _rotate_image(self, angle: int):
        """Rotate the current image by specified angle."""
        if not self.original_pixmap:
            return

        self.current_rotation = (self.current_rotation + angle) % 360

        transform = QTransform()
        transform.rotate(self.current_rotation)

        self.current_pixmap = self.original_pixmap.transformed(
            transform,
            Qt.SmoothTransformation
        )

        if self.pixmap_item:
            self.pixmap_item.setPixmap(self.current_pixmap)
            self.scene.setSceneRect(QRectF(self.current_pixmap.rect()))
            self._fit_to_window()

    def _fit_to_window(self):
        """Fit image to window size."""
        if self.pixmap_item:
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            self.view.zoom_factor = 1.0
            self._update_zoom_label()

    def _show_metadata(self):
        """Show metadata dialog."""
        if self.current_file:
            dialog = MetadataDialog(self.current_file, self)
            dialog.exec()

    def _update_zoom_label(self):
        """Update the zoom percentage display."""
        zoom_percent = int(self.view.zoom_factor * 100)
        self.zoom_label.setText(
            f"Zoom: {zoom_percent}% • Use mouse wheel to zoom • Drag to pan"
        )

    def show_image(self, image_file: ImageFile):
        """Display an image file in the preview."""
        self.current_file = image_file
        self.current_rotation = 0

        try:
            self.original_pixmap = self._load_image_with_exif_fix(image_file.path)

            if self.original_pixmap.isNull():
                self._show_error("Failed to load image")
                return

            self.current_pixmap = self.original_pixmap

            self.scene.clear()
            self.pixmap_item = QGraphicsPixmapItem(self.current_pixmap)
            self.scene.addItem(self.pixmap_item)
            self.scene.setSceneRect(QRectF(self.current_pixmap.rect()))

            self._fit_to_window()

            # Show and enable toolbar
            self.toolbar.show()
            self._position_floating_toolbar()
            self.toolbar.enable_buttons(True)

            # Connect wheel event to update label
            self.view.wheelEvent = self._create_wheel_handler()

        except Exception as e:
            self._show_error(f"Error loading image: {e}")

    def _create_wheel_handler(self):
        """Create custom wheel event handler that updates zoom label."""
        original_wheel = ImageGraphicsView.wheelEvent

        def wheel_handler(event):
            original_wheel(self.view, event)
            self._update_zoom_label()

        return wheel_handler

    def clear_preview(self):
        """Clear the preview display."""
        self.current_file = None
        self.current_pixmap = None
        self.original_pixmap = None
        self.current_rotation = 0
        self.scene.clear()
        self.zoom_label.setText("Use mouse wheel to zoom • Drag to pan")

        if hasattr(self, 'toolbar'):
            self.toolbar.hide()
            self.toolbar.enable_buttons(False)

    def _show_error(self, message: str):
        """Display an error message."""
        self.scene.clear()
        self.zoom_label.setText(message)

        if hasattr(self, 'toolbar'):
            self.toolbar.hide()
            self.toolbar.enable_buttons(False)

    def set_toolbar_icons(self, rotate_left: str, rotate_right: str, fit_window: str, metadata: str):
        """Set custom icons for toolbar buttons."""
        self.toolbar.set_icons(rotate_left, rotate_right, fit_window, metadata)
