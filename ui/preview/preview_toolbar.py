"""
Floating toolbar for preview controls.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton
from PySide6.QtCore import Qt, Signal, QSize, QFile
from PySide6.QtGui import QIcon
from .preview_types import PreviewMode
from utils.logger import logger


class PreviewToolbar(QWidget):
    """Floating toolbar widget with zoom, rotate, and metadata controls."""

    # Signals for button actions
    preview_mode_changed = Signal(PreviewMode)
    output_preview_toggled = Signal(bool)  # Signal for output preview button
    rotate_left_clicked = Signal()
    rotate_right_clicked = Signal()
    fit_to_window_clicked = Signal()
    show_metadata_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("floatingToolbar")

        # Enable styled background for QSS to work
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.current_mode = PreviewMode.PREVIEW  # Start in preview mode
        self._setup_ui()

        logger.debug("Preview toolbar initialized in Preview mode", "PreviewToolbar")

    def _setup_ui(self):
        """Create toolbar buttons and layout."""
        toolbar_layout = QHBoxLayout(self)
        toolbar_layout.setContentsMargins(6, 6, 6, 6)
        toolbar_layout.setSpacing(4)

        button_size = QSize(32, 32)
        icon_size = QSize(16, 16)

        # === HD/Preview Toggle Button (LEFT SIDE) ===
        self.hd_toggle_btn = QToolButton()
        self.hd_toggle_btn.setObjectName("hdToggleButton")
        self.hd_toggle_btn.setToolTip("Show the full resolution of the image")
        self.hd_toggle_btn.setFixedSize(button_size)
        self.hd_toggle_btn.clicked.connect(self._toggle_preview_mode)
        self.hd_toggle_btn.setEnabled(False)
        self.hd_toggle_btn.setCheckable(True)
        self.hd_toggle_btn.setChecked(False)

        # Load HD icon from QRC (no need to check existence)
        hd_icon = QIcon(":/icons/hd-preview.svg")
        if not hd_icon.isNull():
            self.hd_toggle_btn.setIcon(hd_icon)
            self.hd_toggle_btn.setIconSize(icon_size)
            logger.debug("HD preview icon loaded", "PreviewToolbar")
        else:
            self.hd_toggle_btn.setText("HD")  # Fallback text
            logger.warning("HD preview icon not found in QRC", "PreviewToolbar")

        toolbar_layout.addWidget(self.hd_toggle_btn)

        # === OUTPUT PREVIEW Toggle Button ===
        self.output_preview_btn = QToolButton()
        self.output_preview_btn.setObjectName("outputPreviewButton")
        self.output_preview_btn.setToolTip(
            "Toggle Output Preview (shows the final image with applicable settings)\n\n"
            "Applied in preview: Quality, Scale (%), PNG compression, Lossless mode\n"
            "Excluded from preview: Target file size; Advanced options: WebP Method; AVIF Speed"
        )
        self.output_preview_btn.setFixedSize(button_size)
        self.output_preview_btn.clicked.connect(self._on_output_preview_clicked)
        self.output_preview_btn.setEnabled(False)
        self.output_preview_btn.setCheckable(True)
        self.output_preview_btn.setChecked(False)

        # Load preview icon from QRC (no need to check existence)
        preview_icon = QIcon(":/icons/preview.svg")
        if not preview_icon.isNull():
            self.output_preview_btn.setIcon(preview_icon)
            self.output_preview_btn.setIconSize(icon_size)
            logger.debug("Output preview icon loaded", "PreviewToolbar")
        else:
            self.output_preview_btn.setText("OUT")  # Fallback text
            logger.warning("Output preview icon not found in QRC", "PreviewToolbar")

        toolbar_layout.addWidget(self.output_preview_btn)

        # === Existing Buttons (RIGHT SIDE) ===

        # Rotate left button
        self.rotate_left_btn = QToolButton()
        self.rotate_left_btn.setObjectName("toolButton")
        self.rotate_left_btn.setIcon(QIcon(":/icons/rotate_left.svg"))
        self.rotate_left_btn.setIconSize(icon_size)
        self.rotate_left_btn.setToolTip("Rotate Left (90° CCW)")
        self.rotate_left_btn.setFixedSize(button_size)
        self.rotate_left_btn.clicked.connect(self.rotate_left_clicked.emit)
        self.rotate_left_btn.setEnabled(False)

        # Rotate right button
        self.rotate_right_btn = QToolButton()
        self.rotate_right_btn.setObjectName("toolButton")
        self.rotate_right_btn.setIcon(QIcon(":/icons/rotate_right.svg"))
        self.rotate_right_btn.setIconSize(icon_size)
        self.rotate_right_btn.setToolTip("Rotate Right (90° CW)")
        self.rotate_right_btn.setFixedSize(button_size)
        self.rotate_right_btn.clicked.connect(self.rotate_right_clicked.emit)
        self.rotate_right_btn.setEnabled(False)

        # Fit to window button
        self.fit_btn = QToolButton()
        self.fit_btn.setObjectName("toolButton")
        self.fit_btn.setIcon(QIcon(":/icons/center_focus.svg"))
        self.fit_btn.setIconSize(icon_size)
        self.fit_btn.setToolTip("Fit to Window")
        self.fit_btn.setFixedSize(button_size)
        self.fit_btn.clicked.connect(self.fit_to_window_clicked.emit)
        self.fit_btn.setEnabled(False)

        # Metadata button
        self.metadata_btn = QToolButton()
        self.metadata_btn.setObjectName("toolButton")
        self.metadata_btn.setIcon(QIcon(":/icons/meta-info.svg"))
        self.metadata_btn.setIconSize(icon_size)
        self.metadata_btn.setToolTip("Show Metadata")
        self.metadata_btn.setFixedSize(button_size)
        self.metadata_btn.clicked.connect(self.show_metadata_clicked.emit)
        self.metadata_btn.setEnabled(False)

        # Add buttons to layout
        toolbar_layout.addWidget(self.rotate_left_btn)
        toolbar_layout.addWidget(self.rotate_right_btn)
        toolbar_layout.addWidget(self.fit_btn)
        toolbar_layout.addWidget(self.metadata_btn)

    def _toggle_preview_mode(self):
        """
        Toggle between Preview and HD modes.

        MODIFIED: Now implements mutual exclusion with output preview button.
        """
        # If HD button is clicked and it's being checked
        if self.hd_toggle_btn.isChecked():
            # Turn OFF output preview button (mutual exclusion)
            self.output_preview_btn.setChecked(False)
            self.current_mode = PreviewMode.HD
            logger.info("Switched to HD mode (full resolution)", "PreviewToolbar")
        else:
            # HD button unchecked - revert to default preview
            self.current_mode = PreviewMode.PREVIEW
            logger.info("Switched to Preview mode (optimized)", "PreviewToolbar")

        self.preview_mode_changed.emit(self.current_mode)

    def _on_output_preview_clicked(self):
        """
        Handle output preview button click.

        NEW: Implements mutual exclusion with HD button.
        """
        # If output preview button is being checked
        if self.output_preview_btn.isChecked():
            # Turn OFF HD button (mutual exclusion)
            self.hd_toggle_btn.setChecked(False)
            self.current_mode = PreviewMode.OUTPUT_PREVIEW
            logger.info("Output preview enabled (settings will be applied)", "PreviewToolbar")
        else:
            # Output preview button unchecked - revert to default preview
            self.current_mode = PreviewMode.PREVIEW
            logger.info("Output preview disabled (reverted to thumbnail)", "PreviewToolbar")

        # Emit signal so MainWindow knows to generate/clear preview
        self.output_preview_toggled.emit(self.output_preview_btn.isChecked())

    def set_preview_mode(self, mode: PreviewMode):
        """Set the current preview mode (programmatically)."""
        self.current_mode = mode
        self.hd_toggle_btn.setChecked(mode == PreviewMode.HD)
        self.output_preview_btn.setChecked(mode == PreviewMode.OUTPUT_PREVIEW)
        logger.debug(f"Preview mode set to: {mode.value}", "PreviewToolbar")

    def enable_buttons(self, enabled: bool):
        """Enable or disable all toolbar buttons."""
        self.hd_toggle_btn.setEnabled(enabled)
        self.output_preview_btn.setEnabled(enabled)
        self.rotate_left_btn.setEnabled(enabled)
        self.rotate_right_btn.setEnabled(enabled)
        self.fit_btn.setEnabled(enabled)
        self.metadata_btn.setEnabled(enabled)

    def set_icons(self, rotate_left: str, rotate_right: str, fit_window: str, metadata: str):
        """
        Set custom icons for toolbar buttons (excluding HD toggle which uses fixed icon).
        Note: This method is for backwards compatibility if needed, but QRC paths should be used directly.
        """
        # For QRC resources, directly create QIcon
        rotate_left_icon = QIcon(rotate_left)
        if not rotate_left_icon.isNull():
            self.rotate_left_btn.setIcon(rotate_left_icon)

        rotate_right_icon = QIcon(rotate_right)
        if not rotate_right_icon.isNull():
            self.rotate_right_btn.setIcon(rotate_right_icon)

        fit_window_icon = QIcon(fit_window)
        if not fit_window_icon.isNull():
            self.fit_btn.setIcon(fit_window_icon)

        metadata_icon = QIcon(metadata)
        if not metadata_icon.isNull():
            self.metadata_btn.setIcon(metadata_icon)
