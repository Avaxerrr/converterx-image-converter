"""
Resize settings widget for image conversion.

Handles resize modes: None and Percentage scaling.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QCheckBox, QRadioButton, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from core.format_settings import ResizeMode


class ResizeSettingsWidget(QWidget):
    """Widget for resize-related settings."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image_width = None
        self.current_image_height = None
        self._setup_ui()

    def _setup_ui(self):
        """Build the resize settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Current image info label
        self.current_dims_label = QLabel("No image selected")
        self.current_dims_label.setObjectName("dims-info-label")
        self.current_dims_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_dims_label)

        # Radio buttons for resize mode
        self.resize_none = QRadioButton("No resize")
        self.resize_none.setChecked(True)
        self.resize_none.toggled.connect(self._on_resize_mode_changed)

        self.resize_percentage = QRadioButton("Scale by %")
        self.resize_percentage.toggled.connect(self._on_resize_mode_changed)

        layout.addWidget(self.resize_none)
        layout.addWidget(self.resize_percentage)

        # Percentage slider container
        self.percentage_container = QWidget()
        percentage_layout = QVBoxLayout(self.percentage_container)
        percentage_layout.setContentsMargins(16, 0, 0, 0)
        percentage_layout.setSpacing(4)

        percentage_label_layout = QHBoxLayout()
        percentage_label_layout.addWidget(QLabel("Scale:"))
        self.percentage_value_label = QLabel("100%")
        self.percentage_value_label.setProperty("class", "value-label")
        percentage_label_layout.addWidget(self.percentage_value_label)
        percentage_label_layout.addStretch()
        percentage_layout.addLayout(percentage_label_layout)

        self.percentage_slider = QSlider(Qt.Horizontal)
        self.percentage_slider.setMinimum(10)
        self.percentage_slider.setMaximum(100)
        self.percentage_slider.setValue(100)
        self.percentage_slider.valueChanged.connect(self._on_percentage_changed)
        percentage_layout.addWidget(self.percentage_slider)

        # Preview label for percentage mode
        self.percentage_preview_label = QLabel("Output: 2000 × 1500 px")
        self.percentage_preview_label.setObjectName("resize-preview-label")
        self.percentage_preview_label.setAlignment(Qt.AlignCenter)
        percentage_layout.addWidget(self.percentage_preview_label)

        layout.addWidget(self.percentage_container)
        self.percentage_container.hide()

    def _on_resize_mode_changed(self):
        """Handle resize mode change."""
        if self.resize_none.isChecked():
            self.percentage_container.hide()
        elif self.resize_percentage.isChecked():
            self.percentage_container.show()

        self._update_resize_preview()
        self.settings_changed.emit()

    def _on_percentage_changed(self, value: int):
        """Handle percentage slider change."""
        self.percentage_value_label.setText(f"{value}%")
        self._update_resize_preview()
        self.settings_changed.emit()

    def _update_resize_preview(self):
        """Calculate and display the output dimensions preview."""
        if not self.current_image_width or not self.current_image_height:
            # No image selected
            self.percentage_preview_label.setText("Select an image to preview")
            self.percentage_preview_label.setStyleSheet("color: #858585;")
            return

        # Calculate based on resize mode
        if self.resize_none.isChecked():
            # No resize - output = input
            pass

        elif self.resize_percentage.isChecked():
            # Percentage scaling
            scale = self.percentage_slider.value() / 100.0
            output_width = int(self.current_image_width * scale)
            output_height = int(self.current_image_height * scale)

            preview_text = f"→ Output: {output_width} × {output_height} px"
            self.percentage_preview_label.setText(preview_text)

            # Warning if upscaling
            if scale > 1.0:
                self.percentage_preview_label.setStyleSheet("color: #f48771;")  # Warning color
            else:
                self.percentage_preview_label.setStyleSheet("color: #4ec9b0;")  # Success color

    def get_settings(self) -> dict:
        """Get current resize settings as a dictionary."""
        if self.resize_none.isChecked():
            resize_mode = ResizeMode.NONE
        else:
            resize_mode = ResizeMode.PERCENTAGE

        settings = {
            'resize_mode': resize_mode,
            'resize_percentage': self.percentage_slider.value()
        }

        return settings

    def set_current_image(self, width: int, height: int):
        """Update with current image dimensions for preview calculations."""
        self.current_image_width = width
        self.current_image_height = height

        if width and height:
            self.current_dims_label.setText(f"Original: {width} × {height} px")
            self.current_dims_label.setStyleSheet("color: #cccccc;")
        else:
            self.current_dims_label.setText("No image selected")
            self.current_dims_label.setStyleSheet("color: #858585;")

        self._update_resize_preview()

    def clear_current_image(self):
        """Clear current image dimensions."""
        self.current_image_width = None
        self.current_image_height = None
        self.current_dims_label.setText("No image selected")
        self.current_dims_label.setStyleSheet("color: #858585;")
        self._update_resize_preview()
