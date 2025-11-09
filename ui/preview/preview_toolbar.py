"""
Floating toolbar for preview controls.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from pathlib import Path
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

        # CRITICAL: Enable styled background for QSS to work
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

        # === HD/Preview Toggle Button (LEFT SIDE) ===
        self.hd_toggle_btn = QToolButton()
        self.hd_toggle_btn.setObjectName("hdToggleButton")  # Special objectName for styling
        self.hd_toggle_btn.setToolTip("Show the full resolution of the image")
        self.hd_toggle_btn.setFixedSize(button_size)
        self.hd_toggle_btn.clicked.connect(self._toggle_preview_mode)
        self.hd_toggle_btn.setEnabled(False)
        self.hd_toggle_btn.setCheckable(True)  # Make it a toggle button
        self.hd_toggle_btn.setChecked(False)   # Start unchecked (Preview mode)

        # Try to load icon
        icon_path = Path("icons/hd-preview.svg")
        if icon_path.exists():
            self.hd_toggle_btn.setIcon(QIcon(str(icon_path)))
            self.hd_toggle_btn.setIconSize(QSize(16, 16))
        else:
            self.hd_toggle_btn.setText("HD")  # Fallback text
            logger.warning(f"HD preview icon not found: {icon_path}", "PreviewToolbar")

        toolbar_layout.addWidget(self.hd_toggle_btn)

        # === OUTPUT PREVIEW Toggle Button ===
        self.output_preview_btn = QToolButton()
        self.output_preview_btn.setObjectName("outputPreviewButton")
        # More detailed tooltip
        self.output_preview_btn.setToolTip(
            "Toggle Output Preview (Show the final look of the image with settings applied)\n\n"
            "Applied: Quality, Scale %, PNG compression, Lossless\n"
            "Excluded: Target file size, Advanced options"
        )
        self.output_preview_btn.setFixedSize(button_size)
        self.output_preview_btn.clicked.connect(self._on_output_preview_clicked)
        self.output_preview_btn.setEnabled(False)
        self.output_preview_btn.setCheckable(True)  # Make it a toggle button
        self.output_preview_btn.setChecked(False)  # Start unchecked

        # Try to load icon
        output_icon_path = Path("icons/preview.svg")
        if output_icon_path.exists():
            self.output_preview_btn.setIcon(QIcon(str(output_icon_path)))
            self.output_preview_btn.setIconSize(QSize(16, 16))
            logger.debug(f"Output preview icon loaded: {output_icon_path}", "PreviewToolbar")
        else:
            self.output_preview_btn.setText("OUT")  # Fallback text
            logger.warning(f"Output preview icon not found: {output_icon_path}", "PreviewToolbar")

        toolbar_layout.addWidget(self.output_preview_btn)

        # === Existing Buttons (RIGHT SIDE) ===

        # Rotate left button
        self.rotate_left_btn = QToolButton()
        self.rotate_left_btn.setObjectName("toolButton")
        self.rotate_left_btn.setText("↶")
        self.rotate_left_btn.setToolTip("Rotate Left (90° CCW)")
        self.rotate_left_btn.setFixedSize(button_size)
        self.rotate_left_btn.clicked.connect(self.rotate_left_clicked.emit)
        self.rotate_left_btn.setEnabled(False)

        # Rotate right button
        self.rotate_right_btn = QToolButton()
        self.rotate_right_btn.setObjectName("toolButton")
        self.rotate_right_btn.setText("↷")
        self.rotate_right_btn.setToolTip("Rotate Right (90° CW)")
        self.rotate_right_btn.setFixedSize(button_size)
        self.rotate_right_btn.clicked.connect(self.rotate_right_clicked.emit)
        self.rotate_right_btn.setEnabled(False)

        # Fit to window button
        self.fit_btn = QToolButton()
        self.fit_btn.setObjectName("toolButton")
        self.fit_btn.setText("⛶")
        self.fit_btn.setToolTip("Fit to Window")
        self.fit_btn.setFixedSize(button_size)
        self.fit_btn.clicked.connect(self.fit_to_window_clicked.emit)
        self.fit_btn.setEnabled(False)

        # Metadata button
        self.metadata_btn = QToolButton()
        self.metadata_btn.setObjectName("toolButton")
        self.metadata_btn.setText("ⓘ")
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
        self.output_preview_btn.setEnabled(enabled)  # Enable/disable output preview button
        self.rotate_left_btn.setEnabled(enabled)
        self.rotate_right_btn.setEnabled(enabled)
        self.fit_btn.setEnabled(enabled)
        self.metadata_btn.setEnabled(enabled)

    def set_icons(self, rotate_left: str, rotate_right: str, fit_window: str, metadata: str):
        """Set custom icons for toolbar buttons (excluding HD toggle which uses fixed icon)."""
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
