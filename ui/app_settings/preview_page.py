"""
Preview Settings Page

Settings page for preview-related configuration:
- Preview Cache Size
- HD Cache Size
- Preview Max Dimension
- Output Preview Debounce
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController


class PreviewSettingsPage(QWidget):
    """
    Settings page for preview configuration.

    Controls preview caching, image sizing, and debounce timing.
    """

    def __init__(self, controller: 'AppSettingsController'):
        """
        Initialize preview settings page.

        Args:
            controller: AppSettingsController instance (injected dependency)
        """
        super().__init__()
        self.controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build UI with spinboxes for preview settings."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # ============================================================
        # Title
        # ============================================================
        title = QLabel("Preview Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # ============================================================
        # Preview Cache Size
        # ============================================================
        preview_cache_group = QGroupBox("Preview Cache")
        preview_cache_layout = QVBoxLayout()
        preview_cache_layout.setSpacing(8)

        cache_label = QLabel("Preview Cache Size")
        cache_label.setStyleSheet("font-weight: 500;")

        self.preview_cache_spinbox = QSpinBox()
        self.preview_cache_spinbox.setRange(1, 50)
        self.preview_cache_spinbox.setValue(10)
        self.preview_cache_spinbox.setFixedWidth(100)
        self.preview_cache_spinbox.setToolTip(
            "Number of preview images kept in memory.\n"
            "Higher values use more RAM but reduce loading times.\n"
            "Range: 1-50"
        )

        cache_help = QLabel("Number of preview images kept in memory")
        cache_help.setStyleSheet("color: #858585; font-size: 11px;")
        cache_help.setWordWrap(True)

        preview_cache_layout.addWidget(cache_label)
        preview_cache_layout.addWidget(self.preview_cache_spinbox)
        preview_cache_layout.addWidget(cache_help)
        preview_cache_group.setLayout(preview_cache_layout)
        layout.addWidget(preview_cache_group)

        # ============================================================
        # HD Cache Size
        # ============================================================
        hd_cache_group = QGroupBox("HD Cache")
        hd_cache_layout = QVBoxLayout()
        hd_cache_layout.setSpacing(8)

        hd_label = QLabel("HD Cache Size")
        hd_label.setStyleSheet("font-weight: 500;")

        self.hd_cache_spinbox = QSpinBox()
        self.hd_cache_spinbox.setRange(1, 20)
        self.hd_cache_spinbox.setValue(2)
        self.hd_cache_spinbox.setFixedWidth(100)
        self.hd_cache_spinbox.setToolTip(
            "Number of full-resolution images kept in memory.\n"
            "Higher values use significantly more RAM.\n"
            "Range: 1-20"
        )

        hd_help = QLabel("Number of full-resolution images kept in memory")
        hd_help.setStyleSheet("color: #858585; font-size: 11px;")
        hd_help.setWordWrap(True)

        hd_cache_layout.addWidget(hd_label)
        hd_cache_layout.addWidget(self.hd_cache_spinbox)
        hd_cache_layout.addWidget(hd_help)
        hd_cache_group.setLayout(hd_cache_layout)
        layout.addWidget(hd_cache_group)

        # ============================================================
        # Preview Max Dimension
        # ============================================================
        dimension_group = QGroupBox("Preview Quality")
        dimension_layout = QVBoxLayout()
        dimension_layout.setSpacing(8)

        dimension_label = QLabel("Preview Max Dimension")
        dimension_label.setStyleSheet("font-weight: 500;")

        self.dimension_spinbox = QSpinBox()
        self.dimension_spinbox.setRange(720, 4096)
        self.dimension_spinbox.setSingleStep(10)
        self.dimension_spinbox.setValue(1500)
        self.dimension_spinbox.setFixedWidth(100)
        self.dimension_spinbox.setSuffix(" px")
        self.dimension_spinbox.setToolTip(
            "Maximum width/height for preview mode.\n"
            "Higher values show more detail but use more memory.\n"
            "Range: 720-4096 pixels"
        )

        dimension_help = QLabel("Maximum width/height for preview mode (in pixels)")
        dimension_help.setStyleSheet("color: #858585; font-size: 11px;")
        dimension_help.setWordWrap(True)

        dimension_layout.addWidget(dimension_label)
        dimension_layout.addWidget(self.dimension_spinbox)
        dimension_layout.addWidget(dimension_help)
        dimension_group.setLayout(dimension_layout)
        layout.addWidget(dimension_group)

        # ============================================================
        # Output Preview Debounce
        # ============================================================
        debounce_group = QGroupBox("Output Preview Timing")
        debounce_layout = QVBoxLayout()
        debounce_layout.setSpacing(8)

        debounce_label = QLabel("Output Preview Delay")
        debounce_label.setStyleSheet("font-weight: 500;")

        self.debounce_spinbox = QSpinBox()
        self.debounce_spinbox.setRange(100, 2000)
        self.debounce_spinbox.setSingleStep(50)
        self.debounce_spinbox.setValue(250)
        self.debounce_spinbox.setFixedWidth(100)
        self.debounce_spinbox.setSuffix(" ms")
        self.debounce_spinbox.setToolTip(
            "Delay before regenerating output preview after settings change.\n"
            "Lower values are more responsive but use more CPU.\n"
            "Range: 100-2000 milliseconds"
        )

        debounce_help = QLabel(
            "Delay before regenerating output preview after settings change (milliseconds)"
        )
        debounce_help.setStyleSheet("color: #858585; font-size: 11px;")
        debounce_help.setWordWrap(True)

        debounce_layout.addWidget(debounce_label)
        debounce_layout.addWidget(self.debounce_spinbox)
        debounce_layout.addWidget(debounce_help)
        debounce_group.setLayout(debounce_layout)
        layout.addWidget(debounce_group)

        # ============================================================
        # Spacer
        # ============================================================
        layout.addStretch()

    def load_from_controller(self) -> None:
        """Load current settings from controller into UI."""
        self.preview_cache_spinbox.setValue(
            self.controller.get_preview_cache_size()
        )
        self.hd_cache_spinbox.setValue(
            self.controller.get_hd_cache_size()
        )
        self.dimension_spinbox.setValue(
            self.controller.get_preview_max_dimension()
        )
        self.debounce_spinbox.setValue(
            self.controller.get_out_preview_debounce()
        )

    def save_to_controller(self) -> None:
        """
        Save UI values back to controller.

        Raises:
            ValueError: If validation fails (re-raised from controller)
        """
        self.controller.set_preview_cache_size(
            self.preview_cache_spinbox.value()
        )
        self.controller.set_hd_cache_size(
            self.hd_cache_spinbox.value()
        )
        self.controller.set_preview_max_dimension(
            self.dimension_spinbox.value()
        )
        self.controller.set_out_preview_debounce(
            self.debounce_spinbox.value()
        )
