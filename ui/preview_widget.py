from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QToolButton
)
from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QPixmap, QTransform, QWheelEvent, QPainter, QImageReader, QIcon
from pathlib import Path
from models.image_file import ImageFile
from ui.metadata_dialog import MetadataDialog


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
        delta = event.angleDelta().y()

        if delta > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15

        new_zoom = self.zoom_factor * factor

        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.zoom_factor = new_zoom


class PreviewWidget(QWidget):
    """Widget for displaying image preview with zoom and rotation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: ImageFile = None
        self.current_pixmap: QPixmap = None
        self.current_rotation: int = 0
        self.original_pixmap: QPixmap = None
        self._setup_ui()
        self._load_stylesheet()

    def _load_stylesheet(self):
        """Load the stylesheet from external QSS file."""
        # Look for QSS in qss/ folder, two levels up from ui/
        style_file = Path(__file__).parent.parent / "qss" / "preview_widget.qss"

        if style_file.exists():
            with open(style_file, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Warning: Stylesheet not found at {style_file}")

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Graphics view for image display
        self.view = ImageGraphicsView()
        self.view.setObjectName("imageView")

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.pixmap_item = None

        layout.addWidget(self.view, stretch=1)

        # Create floating toolbar (will be positioned over the view)
        self._create_floating_toolbar()

        # Zoom info label at bottom
        self.zoom_label = QLabel("Use mouse wheel to zoom • Drag to pan")
        self.zoom_label.setObjectName("zoomLabel")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.zoom_label)

    def _create_floating_toolbar(self):
        """Create a floating toolbar that appears over the image."""
        self.toolbar_widget = QWidget(self.view)
        self.toolbar_widget.setObjectName("floatingToolbar")

        from PySide6.QtWidgets import QHBoxLayout
        toolbar_layout = QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(6, 6, 6, 6)
        toolbar_layout.setSpacing(4)

        button_size = QSize(32, 32)

        # Rotate left
        self.rotate_left_btn = QToolButton()
        self.rotate_left_btn.setObjectName("toolButton")
        self.rotate_left_btn.setText("↶")
        self.rotate_left_btn.setToolTip("Rotate Left (90° CCW)")
        self.rotate_left_btn.setFixedSize(button_size)
        self.rotate_left_btn.clicked.connect(lambda: self._rotate_image(-90))
        self.rotate_left_btn.setEnabled(False)

        # Rotate right
        self.rotate_right_btn = QToolButton()
        self.rotate_right_btn.setObjectName("toolButton")
        self.rotate_right_btn.setText("↷")
        self.rotate_right_btn.setToolTip("Rotate Right (90° CW)")
        self.rotate_right_btn.setFixedSize(button_size)
        self.rotate_right_btn.clicked.connect(lambda: self._rotate_image(90))
        self.rotate_right_btn.setEnabled(False)

        # Fit to window
        self.fit_btn = QToolButton()
        self.fit_btn.setObjectName("toolButton")
        self.fit_btn.setText("⛶")
        self.fit_btn.setToolTip("Fit to Window")
        self.fit_btn.setFixedSize(button_size)
        self.fit_btn.clicked.connect(self._fit_to_window)
        self.fit_btn.setEnabled(False)

        # Metadata button
        self.metadata_btn = QToolButton()
        self.metadata_btn.setObjectName("toolButton")
        self.metadata_btn.setText("ⓘ")
        self.metadata_btn.setToolTip("Show Metadata")
        self.metadata_btn.setFixedSize(button_size)
        self.metadata_btn.clicked.connect(self._show_metadata)
        self.metadata_btn.setEnabled(False)

        toolbar_layout.addWidget(self.rotate_left_btn)
        toolbar_layout.addWidget(self.rotate_right_btn)
        toolbar_layout.addWidget(self.fit_btn)
        toolbar_layout.addWidget(self.metadata_btn)

        # Position toolbar in top-right corner
        self.toolbar_widget.hide()

    def _position_floating_toolbar(self):
        """Position the floating toolbar in the top-right corner."""
        if hasattr(self, 'toolbar_widget'):
            margin = 12
            toolbar_width = self.toolbar_widget.sizeHint().width()
            toolbar_height = self.toolbar_widget.sizeHint().height()

            x = self.view.width() - toolbar_width - margin
            y = margin

            self.toolbar_widget.move(x, y)
            self.toolbar_widget.raise_()

    def resizeEvent(self, event):
        """Handle widget resize to reposition toolbar."""
        super().resizeEvent(event)
        self._position_floating_toolbar()

    def _load_image_with_exif_fix(self, image_path: Path) -> QPixmap:
        """Load image and fix EXIF orientation issues."""
        try:
            reader = QImageReader(str(image_path))
            reader.setAutoTransform(True)
            image = reader.read()

            if image.isNull():
                print(f"Failed to read image: {reader.errorString()}")
                return QPixmap()

            return QPixmap.fromImage(image)

        except Exception as e:
            print(f"Error loading image with EXIF fix: {e}")
            return QPixmap(str(image_path))

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
            self.toolbar_widget.show()
            self._position_floating_toolbar()
            self.rotate_left_btn.setEnabled(True)
            self.rotate_right_btn.setEnabled(True)
            self.fit_btn.setEnabled(True)
            self.metadata_btn.setEnabled(True)

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

        if hasattr(self, 'toolbar_widget'):
            self.toolbar_widget.hide()

        self.rotate_left_btn.setEnabled(False)
        self.rotate_right_btn.setEnabled(False)
        self.fit_btn.setEnabled(False)
        self.metadata_btn.setEnabled(False)

    def _show_error(self, message: str):
        """Display an error message."""
        self.scene.clear()
        self.zoom_label.setText(message)

        if hasattr(self, 'toolbar_widget'):
            self.toolbar_widget.hide()

        self.rotate_left_btn.setEnabled(False)
        self.rotate_right_btn.setEnabled(False)
        self.fit_btn.setEnabled(False)
        self.metadata_btn.setEnabled(False)

    def set_toolbar_icons(self, rotate_left: str, rotate_right: str, fit_window: str, metadata: str):
        """Set custom icons for toolbar buttons."""
        if Path(rotate_left).exists():
            self.rotate_left_btn.setIcon(QIcon(rotate_left))
            self.rotate_left_btn.setText("")

        if Path(rotate_right).exists():
            self.rotate_right_btn.setIcon(QIcon(rotate_right))
            self.rotate_right_btn.setText("")

        if Path(fit_window).exists():
            self.fit_btn.setIcon(QIcon(fit_window))
            self.fit_btn.setText("")

        if Path(metadata).exists():
            self.metadata_btn.setIcon(QIcon(metadata))
            self.metadata_btn.setText("")
