"""
Advanced settings widget for format-specific options.

Shows/hides different advanced options based on the selected format.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QPushButton
)
from PySide6.QtCore import Signal
from core.format_settings import ImageFormat


class AdvancedSettingsWidget(QWidget):
    """Widget for format-specific advanced settings."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_format = ImageFormat.WEBP
        self._setup_ui()

    def _setup_ui(self):
        """Build the advanced settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # WebP Method
        webp_method_layout = QHBoxLayout()
        webp_method_layout.addWidget(QLabel("Method:"))
        self.webp_method_spin = QSpinBox()
        self.webp_method_spin.setMinimum(0)
        self.webp_method_spin.setMaximum(6)
        self.webp_method_spin.setValue(6)
        self.webp_method_spin.setToolTip("0=Fast, 6=Best quality")
        self.webp_method_spin.valueChanged.connect(lambda: self.settings_changed.emit())  # FIXED
        webp_method_layout.addWidget(self.webp_method_spin)
        webp_method_layout.addStretch()
        self.webp_method_widget = QWidget()
        self.webp_method_widget.setLayout(webp_method_layout)
        layout.addWidget(self.webp_method_widget)

        # WebP Subsampling
        webp_subsampling_layout = QHBoxLayout()
        webp_subsampling_layout.addWidget(QLabel("Subsampling:"))
        self.webp_subsampling_combo = QComboBox()
        self.webp_subsampling_combo.addItems(["4:4:4", "4:2:2", "4:2:0"])
        self.webp_subsampling_combo.setCurrentIndex(2)  # Default to 4:2:0
        self.webp_subsampling_combo.setToolTip("Chroma subsampling (4:4:4=Best, 4:2:0=Smallest)")
        self.webp_subsampling_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())  # FIXED
        webp_subsampling_layout.addWidget(self.webp_subsampling_combo)
        webp_subsampling_layout.addStretch()
        self.webp_subsampling_widget = QWidget()
        self.webp_subsampling_widget.setLayout(webp_subsampling_layout)
        layout.addWidget(self.webp_subsampling_widget)

        # AVIF Speed
        avif_speed_layout = QHBoxLayout()
        avif_speed_layout.addWidget(QLabel("Speed:"))
        self.avif_speed_spin = QSpinBox()
        self.avif_speed_spin.setMinimum(0)
        self.avif_speed_spin.setMaximum(10)
        self.avif_speed_spin.setValue(4)
        self.avif_speed_spin.setToolTip("0=Slowest/Best, 10=Fastest")
        self.avif_speed_spin.valueChanged.connect(lambda: self.settings_changed.emit())  # FIXED
        avif_speed_layout.addWidget(self.avif_speed_spin)
        avif_speed_layout.addStretch()
        self.avif_speed_widget = QWidget()
        self.avif_speed_widget.setLayout(avif_speed_layout)
        layout.addWidget(self.avif_speed_widget)

        # AVIF Range
        avif_range_layout = QHBoxLayout()
        avif_range_layout.addWidget(QLabel("Range:"))
        self.avif_range_combo = QComboBox()
        self.avif_range_combo.addItems(["Limited", "Full"])
        self.avif_range_combo.setCurrentIndex(1)  # Default to Full
        self.avif_range_combo.setToolTip("Color range (Full=Better quality)")
        self.avif_range_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())  # FIXED
        avif_range_layout.addWidget(self.avif_range_combo)
        avif_range_layout.addStretch()
        self.avif_range_widget = QWidget()
        self.avif_range_widget.setLayout(avif_range_layout)
        layout.addWidget(self.avif_range_widget)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("reset-button")
        reset_btn.clicked.connect(self._reset_advanced_settings)
        layout.addWidget(reset_btn)

        # Initially hide all (will be shown based on format)
        self._update_visibility()

    def _reset_advanced_settings(self):
        """Reset advanced settings to defaults."""
        # WebP defaults
        self.webp_method_spin.setValue(6)
        self.webp_subsampling_combo.setCurrentIndex(2)  # 4:2:0

        # AVIF defaults
        self.avif_speed_spin.setValue(4)
        self.avif_range_combo.setCurrentIndex(1)  # Full

        self.settings_changed.emit()

    def set_active_format(self, format_enum: ImageFormat):
        """Show/hide relevant settings based on active format."""
        self.current_format = format_enum
        self._update_visibility()

    def _update_visibility(self):
        """Update widget visibility based on current format."""
        if self.current_format == ImageFormat.WEBP:
            self.webp_method_widget.show()
            self.webp_subsampling_widget.show()
            self.avif_speed_widget.hide()
            self.avif_range_widget.hide()
        elif self.current_format == ImageFormat.AVIF:
            self.webp_method_widget.hide()
            self.webp_subsampling_widget.hide()
            self.avif_speed_widget.show()
            self.avif_range_widget.show()
        else:  # JPEG, PNG, or others
            # Hide all advanced options for JPEG/PNG
            self.webp_method_widget.hide()
            self.webp_subsampling_widget.hide()
            self.avif_speed_widget.hide()
            self.avif_range_widget.hide()

    def get_settings(self) -> dict:
        """Get current advanced settings as a dictionary."""
        settings = {}

        if self.current_format == ImageFormat.WEBP:
            settings['webp_method'] = self.webp_method_spin.value()
            # Convert subsampling to tuple format Pillow expects
            subsampling_map = {"4:4:4": (1, 1), "4:2:2": (2, 1), "4:2:0": (2, 2)}
            settings['webp_subsampling'] = subsampling_map[self.webp_subsampling_combo.currentText()]

        elif self.current_format == ImageFormat.AVIF:
            settings['avif_speed'] = self.avif_speed_spin.value()
            settings['avif_range'] = self.avif_range_combo.currentText().lower()

        return settings

    def should_show_for_format(self, format_enum: ImageFormat) -> bool:
        """Check if advanced settings should be shown for this format."""
        return format_enum in [ImageFormat.WEBP, ImageFormat.AVIF]
