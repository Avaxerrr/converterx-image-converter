"""
Floating toolbar for preview controls.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from pathlib import Path


class PreviewToolbar(QWidget):
    """Floating toolbar widget with zoom, rotate, and metadata controls."""

    # Signals for button actions
    rotate_left_clicked = Signal()
    rotate_right_clicked = Signal()
    fit_to_window_clicked = Signal()
    show_metadata_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("floatingToolbar")

        # CRITICAL: Enable styled background for QSS to work
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._setup_ui()

    def _setup_ui(self):
        """Create toolbar buttons and layout."""
        toolbar_layout = QHBoxLayout(self)
        toolbar_layout.setContentsMargins(6, 6, 6, 6)
        toolbar_layout.setSpacing(4)

        button_size = QSize(32, 32)

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

    def enable_buttons(self, enabled: bool):
        """Enable or disable all toolbar buttons."""
        self.rotate_left_btn.setEnabled(enabled)
        self.rotate_right_btn.setEnabled(enabled)
        self.fit_btn.setEnabled(enabled)
        self.metadata_btn.setEnabled(enabled)

    def set_icons(self, rotate_left: str, rotate_right: str, fit_window: str, metadata: str):
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
