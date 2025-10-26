from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QTransform, QWheelEvent, QPainter, QImageReader
from pathlib import Path
from models.image_file import ImageFile


class ImageGraphicsView(QGraphicsView):
    """Custom QGraphicsView with zoom capabilities."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

        # View settings
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        # Get wheel direction
        delta = event.angleDelta().y()

        if delta > 0:
            # Zoom in
            factor = 1.15
        else:
            # Zoom out
            factor = 1 / 1.15

        # Calculate new zoom level
        new_zoom = self.zoom_factor * factor

        # Clamp zoom level
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.zoom_factor = new_zoom


class PreviewWidget(QWidget):
    """Widget for displaying image preview with zoom and rotation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: ImageFile = None
        self.current_pixmap: QPixmap = None
        self.current_rotation: int = 0  # 0, 90, 180, 270
        self.original_pixmap: QPixmap = None  # Store original for rotation
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Top bar with info and controls
        top_bar = QHBoxLayout()

        # Info label
        self.info_label = QLabel("No image selected")
        self.info_label.setStyleSheet(
            "font-size: 11pt; padding: 8px; "
            "background-color: #252526; border-radius: 4px;"
        )
        self.info_label.setWordWrap(True)
        top_bar.addWidget(self.info_label, stretch=1)

        # Rotation buttons
        self.rotate_left_btn = QPushButton("↶ Rotate Left")
        self.rotate_left_btn.clicked.connect(lambda: self._rotate_image(-90))
        self.rotate_left_btn.setEnabled(False)

        self.rotate_right_btn = QPushButton("↷ Rotate Right")
        self.rotate_right_btn.clicked.connect(lambda: self._rotate_image(90))
        self.rotate_right_btn.setEnabled(False)

        # Zoom controls
        self.fit_btn = QPushButton("Fit to Window")
        self.fit_btn.clicked.connect(self._fit_to_window)
        self.fit_btn.setEnabled(False)

        self.actual_btn = QPushButton("100%")
        self.actual_btn.clicked.connect(self._actual_size)
        self.actual_btn.setEnabled(False)

        top_bar.addWidget(self.rotate_left_btn)
        top_bar.addWidget(self.rotate_right_btn)
        top_bar.addWidget(self.fit_btn)
        top_bar.addWidget(self.actual_btn)

        layout.addLayout(top_bar)

        # Graphics view for image display
        self.view = ImageGraphicsView()
        self.view.setStyleSheet(
            "QGraphicsView { background-color: #252526; border: 1px solid #3e3e42; border-radius: 4px; }"
        )

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.pixmap_item = None

        layout.addWidget(self.view, stretch=1)

        # Zoom info label
        self.zoom_label = QLabel("Use mouse wheel to zoom • Drag to pan")
        self.zoom_label.setStyleSheet("color: #808080; font-size: 9pt;")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.zoom_label)

    def _load_image_with_exif_fix(self, image_path: Path) -> QPixmap:
        """Load image and fix EXIF orientation issues using Qt native support."""
        try:
            # Use QImageReader with auto-transform for EXIF orientation
            reader = QImageReader(str(image_path))
            reader.setAutoTransform(True)  # Handle EXIF orientation automatically

            image = reader.read()

            if image.isNull():
                print(f"Failed to read image: {reader.errorString()}")
                return QPixmap()

            # Convert QImage to QPixmap
            return QPixmap.fromImage(image)

        except Exception as e:
            print(f"Error loading image with EXIF fix: {e}")
            # Fallback to direct loading
            return QPixmap(str(image_path))

    def _rotate_image(self, angle: int):
        """Rotate the current image by specified angle."""
        if not self.original_pixmap:
            return

        self.current_rotation = (self.current_rotation + angle) % 360

        # Create transform for rotation
        transform = QTransform()
        transform.rotate(self.current_rotation)

        # Apply rotation to original pixmap
        self.current_pixmap = self.original_pixmap.transformed(
            transform,
            Qt.SmoothTransformation
        )

        # Update display
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

    def _actual_size(self):
        """Reset to 100% zoom."""
        if self.pixmap_item:
            self.view.resetTransform()
            self.view.zoom_factor = 1.0
            self._update_zoom_label()

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
            # Load image with EXIF fix
            self.original_pixmap = self._load_image_with_exif_fix(image_file.path)

            if self.original_pixmap.isNull():
                self._show_error("Failed to load image")
                return

            self.current_pixmap = self.original_pixmap

            # Clear scene and add new pixmap
            self.scene.clear()
            self.pixmap_item = QGraphicsPixmapItem(self.current_pixmap)
            self.scene.addItem(self.pixmap_item)
            self.scene.setSceneRect(QRectF(self.current_pixmap.rect()))

            # Fit to window initially
            self._fit_to_window()

            # Enable controls
            self.rotate_left_btn.setEnabled(True)
            self.rotate_right_btn.setEnabled(True)
            self.fit_btn.setEnabled(True)
            self.actual_btn.setEnabled(True)

            # Update info label
            info_text = (
                f"<b>{image_file.filename}</b><br>"
                f"{image_file.dimensions_str} px  •  {image_file.size_str}  •  {image_file.format}"
            )
            self.info_label.setText(info_text)

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
        self.info_label.setText("No image selected")
        self.zoom_label.setText("Use mouse wheel to zoom • Drag to pan")

        # Disable controls
        self.rotate_left_btn.setEnabled(False)
        self.rotate_right_btn.setEnabled(False)
        self.fit_btn.setEnabled(False)
        self.actual_btn.setEnabled(False)

    def _show_error(self, message: str):
        """Display an error message."""
        self.scene.clear()
        self.info_label.setText(f"<span style='color: #f48771;'>{message}</span>")

        # Disable controls
        self.rotate_left_btn.setEnabled(False)
        self.rotate_right_btn.setEnabled(False)
        self.fit_btn.setEnabled(False)
        self.actual_btn.setEnabled(False)
