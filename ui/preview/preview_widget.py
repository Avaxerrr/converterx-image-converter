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
from typing import Dict
from models.image_file import ImageFile
from ui.metadata_dialog import MetadataDialog
from .image_graphics_view import ImageGraphicsView
from .preview_toolbar import PreviewToolbar
from .preview_types import PreviewMode
from utils.logger import logger


class PreviewWidget(QWidget):
    """Widget for displaying image preview with zoom and rotation."""

    # Preview settings
    PREVIEW_MAX_DIMENSION = 1920  # Max width or height for preview mode
    MAX_PREVIEW_CACHE = 10        # Cache up to 10 preview images
    MAX_HD_CACHE = 2              # Cache up to 2 HD images

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: ImageFile = None
        self.current_pixmap: QPixmap = None
        self.current_rotation: int = 0
        self.original_pixmap: QPixmap = None
        self.current_mode: PreviewMode = PreviewMode.PREVIEW
        self.user_preferred_mode: PreviewMode = PreviewMode.PREVIEW  # User's manual choice

        # Image caches (path -> QPixmap)
        self.preview_cache: Dict[Path, QPixmap] = {}
        self.hd_cache: Dict[Path, QPixmap] = {}

        self._setup_ui()
        logger.info(f"Preview widget initialized (max dimension: {self.PREVIEW_MAX_DIMENSION}px)", "PreviewWidget")

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
        self.toolbar.preview_mode_changed.connect(self._on_preview_mode_changed)
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
        """Position the floating toolbar in the top-right corner of the preview area."""
        if hasattr(self, 'toolbar'):
            margin_right = 16
            margin_top = 12

            # Use self.width() instead of self.view.width() for proper positioning
            # relative to the entire PreviewWidget container
            toolbar_width = self.toolbar.sizeHint().width()
            toolbar_height = self.toolbar.sizeHint().height()

            # Position relative to PreviewWidget, not the view
            x = self.width() - toolbar_width - margin_right
            y = margin_top

            self.toolbar.move(x, y)
            self.toolbar.raise_()

            logger.debug(
                f"Toolbar positioned: x={x}, y={y} (widget_width={self.width()}, toolbar_width={toolbar_width})",
                source="PreviewWidget"
            )

    def resizeEvent(self, event):
        """Handle widget resize - update overlay geometry."""
        super().resizeEvent(event)

        # Reposition toolbar when widget resizes
        self._position_floating_toolbar()

        # Update loading overlay geometry
        self._update_loading_overlay_geometry()

    def _image_needs_hd_mode(self, image_file: ImageFile) -> bool:
        """Check if image is large enough to benefit from HD mode."""
        max_dimension = max(image_file.width, image_file.height)
        needs_hd = max_dimension > self.PREVIEW_MAX_DIMENSION
        return needs_hd

    def _load_image_with_exif_fix(self, image_path: Path, preview_mode: bool = False) -> QPixmap:
        """
        Load image using PIL (supports AVIF) and convert to QPixmap with EXIF orientation fix.

        Args:
            image_path: Path to the image file
            preview_mode: If True, downscale to PREVIEW_MAX_DIMENSION for performance
        """
        try:
            from PIL import Image, ImageOps

            # Load with PIL (this supports AVIF via pillow-avif-plugin)
            with Image.open(image_path) as pil_image:
                original_size = (pil_image.width, pil_image.height)

                # Apply EXIF orientation
                pil_image = ImageOps.exif_transpose(pil_image)

                # === PREVIEW MODE: Downscale if needed ===
                if preview_mode:
                    max_dim = max(pil_image.width, pil_image.height)
                    if max_dim > self.PREVIEW_MAX_DIMENSION:
                        # Use thumbnail() - maintains aspect ratio, only downscales
                        pil_image.thumbnail(
                            (self.PREVIEW_MAX_DIMENSION, self.PREVIEW_MAX_DIMENSION),
                            Image.Resampling.LANCZOS
                        )
                        logger.debug(
                            f"Downscaled {image_path.name}: {original_size} → "
                            f"({pil_image.width}×{pil_image.height})",
                            "ImageLoader"
                        )
                    else:
                        logger.debug(
                            f"No downscaling needed for {image_path.name}: "
                            f"{original_size} ≤ {self.PREVIEW_MAX_DIMENSION}px",
                            "ImageLoader"
                        )
                else:
                    logger.debug(f"Loading full resolution: {image_path.name} {original_size}", "ImageLoader")

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
            logger.error(f"Failed to load image {image_path.name}: {e}", "ImageLoader")
            return QPixmap()  # Return empty pixmap on error

    def _get_cached_or_load(self, image_path: Path, mode: PreviewMode) -> QPixmap:
        """Get image from cache or load it (with caching)."""
        cache = self.preview_cache if mode == PreviewMode.PREVIEW else self.hd_cache
        max_cache = self.MAX_PREVIEW_CACHE if mode == PreviewMode.PREVIEW else self.MAX_HD_CACHE
        mode_name = "Preview" if mode == PreviewMode.PREVIEW else "HD"

        # Check cache first
        if image_path in cache:
            logger.debug(f"Cache HIT: {image_path.name} ({mode_name} mode)", "ImageCache")
            return cache[image_path]

        logger.debug(f"Cache MISS: {image_path.name} ({mode_name} mode), loading...", "ImageCache")

        # Load image
        is_preview = (mode == PreviewMode.PREVIEW)
        pixmap = self._load_image_with_exif_fix(image_path, preview_mode=is_preview)

        # Cache it (with size limit)
        if len(cache) >= max_cache:
            # Remove oldest entry (first item)
            oldest_key = next(iter(cache))
            logger.debug(
                f"Cache full ({len(cache)}/{max_cache}), evicting: {oldest_key.name} ({mode_name})",
                "ImageCache"
            )
            del cache[oldest_key]

        cache[image_path] = pixmap
        logger.info(
            f"Cached {image_path.name} ({mode_name} mode) | "
            f"Cache size: {len(cache)}/{max_cache}",
            "ImageCache"
        )

        return pixmap

    def _on_preview_mode_changed(self, mode: PreviewMode):
        """Handle preview mode toggle (user clicked HD button)."""
        # Save user's preference
        self.user_preferred_mode = mode
        mode_name = "HD" if mode == PreviewMode.HD else "Preview"
        logger.info(f"User preference changed to: {mode_name}", "PreviewWidget")

        # Check if current image supports HD mode
        if self.current_file and not self._image_needs_hd_mode(self.current_file):
            logger.warning(
                f"HD mode not available: {self.current_file.filename} is too small "
                f"({self.current_file.width}×{self.current_file.height})",
                "PreviewWidget"
            )
            # Revert toolbar button state
            self.toolbar.set_preview_mode(PreviewMode.PREVIEW)
            return

        self.current_mode = mode

        # Reload current image in new mode
        if self.current_file:
            logger.debug(f"Reloading current image in {mode_name} mode", "PreviewWidget")
            self._reload_current_image()

        # Update zoom label
        self._update_zoom_label()

    def _reload_current_image(self):
        """Reload the current image in the current preview mode."""
        if not self.current_file:
            return

        mode_name = "HD" if self.current_mode == PreviewMode.HD else "Preview"
        logger.debug(f"Reloading image in {mode_name} mode (zoom will reset)", "PreviewWidget")

        # Load image in current mode
        self.original_pixmap = self._get_cached_or_load(
            self.current_file.path,
            self.current_mode
        )

        if self.original_pixmap.isNull():
            logger.error(f"Failed to reload image: {self.current_file.filename}", "PreviewWidget")
            self._show_error("Failed to load image")
            return

        # Re-apply current rotation
        if self.current_rotation != 0:
            logger.debug(f"Re-applying rotation: {self.current_rotation}°", "PreviewWidget")
            transform = QTransform()
            transform.rotate(self.current_rotation)
            self.current_pixmap = self.original_pixmap.transformed(
                transform,
                Qt.SmoothTransformation
            )
        else:
            self.current_pixmap = self.original_pixmap

        # Update display
        if self.pixmap_item:
            self.pixmap_item.setPixmap(self.current_pixmap)
            self.scene.setSceneRect(QRectF(self.current_pixmap.rect()))

            # Always fit to window on mode switch (clean, predictable behavior)
            self._fit_to_window()

            logger.info(f"Image reloaded in {mode_name} mode and fitted to window", "PreviewWidget")

    def _rotate_image(self, angle: int):
        """Rotate the current image by specified angle."""
        if not self.original_pixmap:
            return

        self.current_rotation = (self.current_rotation + angle) % 360
        logger.debug(f"Rotating image: {angle}° (total: {self.current_rotation}°)", "PreviewWidget")

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

        # Show appropriate mode text
        if self.current_file and not self._image_needs_hd_mode(self.current_file):
            # Small image - already at full resolution
            mode_text = f"Full Resolution (≤{self.PREVIEW_MAX_DIMENSION}px)"
        else:
            # Large image - show current mode
            mode_text = "HD Mode (Full Resolution)" if self.current_mode == PreviewMode.HD else "Preview Mode (Optimized)"

        self.zoom_label.setText(
            f"Zoom: {zoom_percent}% • {mode_text} • Use mouse wheel to zoom • Drag to pan"
        )

    def show_image(self, image_file: ImageFile):
        """Display an image file in the preview."""
        self.current_file = image_file
        self.current_rotation = 0

        # Check if this image needs HD mode
        hd_available = self._image_needs_hd_mode(image_file)

        if hd_available:
            # Use user's preferred mode for large images
            self.current_mode = self.user_preferred_mode
            logger.info(
                f"Loading image: {image_file.filename} ({self.current_mode.value} mode, HD available)",
                "PreviewWidget"
            )
        else:
            # Force Preview mode for small images (override preference)
            self.current_mode = PreviewMode.PREVIEW
            logger.info(
                f"Loading image: {image_file.filename} (Preview mode, image is {image_file.width}×{image_file.height}, HD not needed)",
                "PreviewWidget"
            )

        try:
            # Load image in determined mode (with caching)
            self.original_pixmap = self._get_cached_or_load(
                image_file.path,
                self.current_mode
            )

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

            # Update toolbar button state to match current mode
            self.toolbar.set_preview_mode(self.current_mode)

            # Enable/disable HD toggle based on image size
            if hd_available:
                self.toolbar.hd_toggle_btn.setEnabled(True)
                self.toolbar.hd_toggle_btn.setToolTip("Toggle HD Mode (Full Resolution)")
                logger.debug(
                    f"HD mode available for {image_file.filename} "
                    f"({image_file.width}×{image_file.height})",
                    "PreviewWidget"
                )
            else:
                self.toolbar.hd_toggle_btn.setEnabled(False)
                self.toolbar.hd_toggle_btn.setToolTip(
                    f"Image is already at full resolution\n"
                    f"({image_file.width}×{image_file.height} ≤ {self.PREVIEW_MAX_DIMENSION}px)\n"
                    f"HD mode only available for larger images"
                )
                logger.debug(
                    f"HD mode disabled for {image_file.filename} "
                    f"({image_file.width}×{image_file.height} ≤ {self.PREVIEW_MAX_DIMENSION}px)",
                    "PreviewWidget"
                )

            # Connect wheel event to update label
            self.view.wheelEvent = self._create_wheel_handler()

            logger.success(f"Image displayed successfully: {image_file.filename}", "PreviewWidget")

        except Exception as e:
            logger.error(f"Error loading image {image_file.filename}: {e}", "PreviewWidget")
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
        logger.debug("Clearing preview display", "PreviewWidget")

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

    def display_output_preview(self, pixmap: QPixmap):
        """
        Display output preview pixmap (externally generated).

        This is a separate display path from show_image() for output previews.
        Used by MainWindow when output preview is ready from worker thread.

        Args:
            pixmap: Output preview pixmap with settings applied (quality, scale, compression)
        """
        logger.info(
            f"Displaying output preview: {pixmap.width()}×{pixmap.height()}",
            source="PreviewWidget"
        )

        # Clear current display
        self.scene.clear()

        # Store as current pixmap (so rotation/zoom work)
        self.current_pixmap = pixmap
        self.original_pixmap = pixmap  # For rotation to work
        self.current_rotation = 0  # Reset rotation for new preview

        # Add to scene
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        # Update scene bounds
        self.scene.setSceneRect(QRectF(pixmap.rect()))

        # Fit to window (clean display)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.view.zoom_factor = 1.0

        # ⭐ UPDATED: More informative label with exclusions
        self.zoom_label.setText(
            f"📸 Output Preview (Approx.) • {pixmap.width()} × {pixmap.height()} • "
            f"Settings applied • ⚠ Excludes: Target size, Method/Speed • "
            f"Use mouse wheel to zoom"
        )

        # Make sure toolbar is visible and enabled
        self.toolbar.show()
        self._position_floating_toolbar()
        self.toolbar.enable_buttons(True)

        self._position_floating_toolbar()

        logger.success(
            f"Output preview displayed successfully ({pixmap.width()}×{pixmap.height()})",
            source="PreviewWidget"
        )

    def show_loading_overlay(self, message: str = "Generating output preview..."):
        """
        Show loading overlay on preview widget.

        Args:
            message: Loading message to display
        """
        # Create overlay if it doesn't exist
        if not hasattr(self, 'loading_overlay'):
            self._create_loading_overlay()

        # Update message and show
        self.loading_label.setText(message)
        self.loading_overlay.show()
        self.loading_overlay.raise_()  # Bring to front

        logger.debug(f"Loading overlay shown: {message}", source="PreviewWidget")

    def hide_loading_overlay(self):
        """Hide loading overlay."""
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.hide()
            logger.debug("Loading overlay hidden", source="PreviewWidget")

    def _create_loading_overlay(self):
        """Create the loading overlay widget (called once)."""
        from PySide6.QtWidgets import QLabel
        from PySide6.QtCore import Qt

        # Semi-transparent overlay
        self.loading_overlay = QWidget(self)
        self.loading_overlay.setObjectName("loadingOverlay")  # QSS styling

        # Loading label
        self.loading_label = QLabel("Generating output preview...", self.loading_overlay)
        self.loading_label.setObjectName("loadingOverlayLabel")  # QSS styling
        self.loading_label.setAlignment(Qt.AlignCenter)

        # Position overlay (will be updated in resizeEvent)
        self._update_loading_overlay_geometry()

        # Start hidden
        self.loading_overlay.hide()

        logger.debug("Loading overlay created", source="PreviewWidget")

    def _update_loading_overlay_geometry(self):
        """Update loading overlay size to match widget."""
        if hasattr(self, 'loading_overlay'):
            # Make overlay cover entire preview area
            self.loading_overlay.setGeometry(self.rect())

            # Center the label
            label_width = 400
            label_height = 100
            x = (self.width() - label_width) // 2
            y = (self.height() - label_height) // 2
            self.loading_label.setGeometry(x, y, label_width, label_height)