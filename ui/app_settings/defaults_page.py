"""
Default Settings Page

Settings page for default conversion settings:
- Default Quality
- Default Output Format
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QComboBox, QGroupBox
)
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController

from core.format_settings import ImageFormat


class DefaultSettingsPage(QWidget):
    """
    Settings page for default conversion configuration.

    Controls default quality and output format when app launches.
    """

    def __init__(self, controller: 'AppSettingsController'):
        """
        Initialize defaults settings page.

        Args:
            controller: AppSettingsController instance (injected dependency)
        """
        super().__init__()
        self.controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build UI with slider for quality and combobox for format."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # ============================================================
        # Title
        # ============================================================
        title = QLabel("Default Conversion Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # ============================================================
        # Default Quality
        # ============================================================
        quality_group = QGroupBox("Quality")
        quality_layout = QVBoxLayout()
        quality_layout.setSpacing(12)

        # Label with dynamic value
        self.quality_label = QLabel("Default Quality: 85")
        self.quality_label.setStyleSheet("font-weight: 500; font-size: 14px;")

        # Slider
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.setToolTip(
            "Default quality for new conversions.\n"
            "Higher values = better quality but larger file size.\n"
            "Range: 1-100"
        )

        # Connect slider to update label
        self.quality_slider.valueChanged.connect(
            lambda v: self.quality_label.setText(f"Default Quality: {v}")
        )

        # Help text
        quality_help = QLabel("Starting quality when app launches (applies to new conversions)")
        quality_help.setStyleSheet("color: #858585; font-size: 11px;")
        quality_help.setWordWrap(True)

        # Add value markers
        markers_layout = QHBoxLayout()
        markers_layout.setContentsMargins(0, 0, 0, 0)

        low_marker = QLabel("Low (1)")
        low_marker.setStyleSheet("color: #858585; font-size: 10px;")

        high_marker = QLabel("High (100)")
        high_marker.setStyleSheet("color: #858585; font-size: 10px;")
        high_marker.setAlignment(Qt.AlignRight)

        markers_layout.addWidget(low_marker)
        markers_layout.addStretch()
        markers_layout.addWidget(high_marker)

        quality_layout.addWidget(self.quality_label)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addLayout(markers_layout)
        quality_layout.addWidget(quality_help)
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)

        # ============================================================
        # Default Output Format
        # ============================================================
        format_group = QGroupBox("Output Format")
        format_layout = QVBoxLayout()
        format_layout.setSpacing(8)

        # Label
        format_label = QLabel("Default Output Format")
        format_label.setStyleSheet("font-weight: 500;")

        # Combobox
        self.format_combo = QComboBox()
        self.format_combo.addItems(["WebP", "AVIF", "JPEG", "PNG"])
        self.format_combo.setFixedWidth(200)
        self.format_combo.setToolTip(
            "Default output format when app launches.\n"
            "WebP: Best balance of size and quality\n"
            "AVIF: Best compression, slower encoding\n"
            "JPEG: Universal compatibility\n"
            "PNG: Lossless, larger files"
        )

        # Help text
        format_help = QLabel("Starting format when app launches (applies to new conversions)")
        format_help.setStyleSheet("color: #858585; font-size: 11px;")
        format_help.setWordWrap(True)

        # Format descriptions
        format_desc = QLabel(
            "• WebP: Modern, efficient (recommended)\n"
            "• AVIF: Best compression, slower\n"
            "• JPEG: Universal compatibility\n"
            "• PNG: Lossless, larger files"
        )
        format_desc.setStyleSheet("color: #858585; font-size: 10px; margin-top: 8px;")

        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addWidget(format_help)
        format_layout.addWidget(format_desc)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # ============================================================
        # Spacer
        # ============================================================
        layout.addStretch()

    def load_from_controller(self) -> None:
        """Load current settings from controller into UI."""
        # Load quality
        self.quality_slider.setValue(
            self.controller.get_default_quality()
        )

        # Load format (convert enum to combobox index)
        format_enum = self.controller.get_default_output_format()
        format_map = {
            ImageFormat.WEBP: 0,
            ImageFormat.AVIF: 1,
            ImageFormat.JPEG: 2,
            ImageFormat.PNG: 3
        }
        self.format_combo.setCurrentIndex(format_map.get(format_enum, 0))

    def save_to_controller(self) -> None:
        """
        Save UI values back to controller.

        Raises:
            ValueError: If validation fails (re-raised from controller)
        """
        # Save quality
        self.controller.set_default_quality(
            self.quality_slider.value()
        )

        # Save format (convert combobox index to enum)
        index_to_format = {
            0: ImageFormat.WEBP,
            1: ImageFormat.AVIF,
            2: ImageFormat.JPEG,
            3: ImageFormat.PNG
        }
        format_enum = index_to_format[self.format_combo.currentIndex()]
        self.controller.set_default_output_format(format_enum)
