"""
Resize settings widget for image conversion.

Handles resize modes: None, Percentage, Fit by Width, Fit by Height, Fit to Dimensions.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QCheckBox, QComboBox, QSpinBox
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
        layout.setSpacing(6)

        # Resize mode dropdown
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Resize:"))

        self.resize_mode_combo = QComboBox()
        self.resize_mode_combo.addItem("None", ResizeMode.NONE)
        self.resize_mode_combo.addItem("Scale by %", ResizeMode.PERCENTAGE)
        self.resize_mode_combo.addItem("Fit by Width", ResizeMode.FIT_TO_WIDTH)
        self.resize_mode_combo.addItem("Fit by Height", ResizeMode.FIT_TO_HEIGHT)
        self.resize_mode_combo.addItem("Fit to Dimensions", ResizeMode.FIT_TO_DIMENSIONS)
        self.resize_mode_combo.currentIndexChanged.connect(self._on_resize_mode_changed)
        mode_layout.addWidget(self.resize_mode_combo, 1)

        layout.addLayout(mode_layout)

        # Original dimensions label (hidden by default)
        self.original_label = QLabel("Original: —")
        self.original_label.setObjectName("dims-info-label")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.hide()
        layout.addWidget(self.original_label)

        # ==== PERCENTAGE CONTAINER ====
        self.percentage_container = QWidget()
        percentage_layout = QVBoxLayout(self.percentage_container)
        percentage_layout.setContentsMargins(0, 4, 0, 4)
        percentage_layout.setSpacing(4)

        percentage_label_layout = QHBoxLayout()
        percentage_label_layout.addWidget(QLabel("Scale:"))
        self.percentage_value_label = QLabel("100%")
        self.percentage_value_label.setProperty("class", "value-label")
        percentage_label_layout.addWidget(self.percentage_value_label)
        percentage_label_layout.addStretch()
        percentage_layout.addLayout(percentage_label_layout)

        self.percentage_slider = QSlider(Qt.Orientation.Horizontal)
        self.percentage_slider.setMinimum(10)
        self.percentage_slider.setMaximum(100)
        self.percentage_slider.setValue(100)
        self.percentage_slider.valueChanged.connect(self._on_percentage_changed)
        percentage_layout.addWidget(self.percentage_slider)

        layout.addWidget(self.percentage_container)
        self.percentage_container.hide()

        # ==== FIT BY WIDTH CONTAINER ====
        self.fit_width_container = QWidget()
        fit_width_layout = QVBoxLayout(self.fit_width_container)
        fit_width_layout.setContentsMargins(0, 4, 0, 4)
        fit_width_layout.setSpacing(4)

        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Target Width:"))
        self.target_width_spinbox = QSpinBox()
        self.target_width_spinbox.setRange(10, 65535)
        self.target_width_spinbox.setValue(1000)
        self.target_width_spinbox.setToolTip("Value from 10-65535px")
        self.target_width_spinbox.setSuffix(" px")
        self.target_width_spinbox.valueChanged.connect(self._on_target_changed)
        width_layout.addWidget(self.target_width_spinbox, 1)
        fit_width_layout.addLayout(width_layout)

        self.fit_width_upscale_checkbox = QCheckBox("Allow upscaling (not recommended)")
        self.fit_width_upscale_checkbox.setToolTip(
            "Upscaling degrades image quality and increases file size.\n"
            "Only enable for specific use cases."
        )
        self.fit_width_upscale_checkbox.stateChanged.connect(self._on_target_changed)
        fit_width_layout.addWidget(self.fit_width_upscale_checkbox)

        layout.addWidget(self.fit_width_container)
        self.fit_width_container.hide()

        # ==== FIT BY HEIGHT CONTAINER ====
        self.fit_height_container = QWidget()
        fit_height_layout = QVBoxLayout(self.fit_height_container)
        fit_height_layout.setContentsMargins(0, 4, 0, 4)
        fit_height_layout.setSpacing(4)

        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Target Height:"))
        self.target_height_spinbox = QSpinBox()
        self.target_height_spinbox.setRange(10, 65535)
        self.target_height_spinbox.setValue(1000)
        self.target_height_spinbox.setToolTip("Value from 10-65535px")
        self.target_height_spinbox.setSuffix(" px")
        self.target_height_spinbox.valueChanged.connect(self._on_target_changed)
        height_layout.addWidget(self.target_height_spinbox, 1)
        fit_height_layout.addLayout(height_layout)

        self.fit_height_upscale_checkbox = QCheckBox("Allow upscaling (not recommended)")
        self.fit_height_upscale_checkbox.setToolTip(
            "Upscaling degrades image quality and increases file size.\n"
            "Only enable for specific use cases."
        )
        self.fit_height_upscale_checkbox.stateChanged.connect(self._on_target_changed)
        fit_height_layout.addWidget(self.fit_height_upscale_checkbox)

        layout.addWidget(self.fit_height_container)
        self.fit_height_container.hide()

        # ==== FIT TO DIMENSIONS CONTAINER ====
        self.dimensions_container = QWidget()
        dimensions_layout = QVBoxLayout(self.dimensions_container)
        dimensions_layout.setContentsMargins(0, 4, 0, 4)
        dimensions_layout.setSpacing(4)

        max_width_layout = QHBoxLayout()
        max_width_layout.addWidget(QLabel("Max Width:"))
        self.max_width_spinbox = QSpinBox()
        self.max_width_spinbox.setRange(10, 65535)
        self.max_width_spinbox.setValue(1920)
        self.max_width_spinbox.setSuffix(" px")
        self.max_width_spinbox.valueChanged.connect(self._on_dimensions_changed)
        max_width_layout.addWidget(self.max_width_spinbox, 1)
        dimensions_layout.addLayout(max_width_layout)

        max_height_layout = QHBoxLayout()
        max_height_layout.addWidget(QLabel("Max Height:"))
        self.max_height_spinbox = QSpinBox()
        self.max_height_spinbox.setRange(10, 65535)
        self.max_height_spinbox.setValue(1080)
        self.max_height_spinbox.setSuffix(" px")
        self.max_height_spinbox.valueChanged.connect(self._on_dimensions_changed)
        max_height_layout.addWidget(self.max_height_spinbox, 1)
        dimensions_layout.addLayout(max_height_layout)

        # Info label for Fit to Dimensions
        self.dimensions_info_label = QLabel("Image fits within box, aspect ratio preserved")
        self.dimensions_info_label.setProperty("class", "info-note")
        self.dimensions_info_label.setWordWrap(True)
        dimensions_layout.addWidget(self.dimensions_info_label)

        self.dimensions_upscale_checkbox = QCheckBox("Allow upscaling (not recommended)")
        self.dimensions_upscale_checkbox.setToolTip(
            "Upscaling degrades image quality and increases file size.\n"
            "Only enable for specific use cases."
        )
        self.dimensions_upscale_checkbox.stateChanged.connect(self._on_dimensions_changed)
        dimensions_layout.addWidget(self.dimensions_upscale_checkbox)

        layout.addWidget(self.dimensions_container)
        self.dimensions_container.hide()

        # Output dimensions label (hidden by default) - uses existing QSS
        self.output_label = QLabel("Output: —")
        self.output_label.setObjectName("resize-preview-label")
        self.output_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_label.hide()
        layout.addWidget(self.output_label)

    def _on_resize_mode_changed(self):
        """Handle resize mode dropdown change."""
        mode = self.resize_mode_combo.currentData()

        # Hide all containers first
        self.original_label.hide()
        self.percentage_container.hide()
        self.fit_width_container.hide()
        self.fit_height_container.hide()
        self.dimensions_container.hide()
        self.output_label.hide()

        if mode == ResizeMode.NONE:
            pass

        elif mode == ResizeMode.PERCENTAGE:
            self.original_label.show()
            self.percentage_container.show()
            self.output_label.show()

        elif mode == ResizeMode.FIT_TO_WIDTH:
            self.original_label.show()
            self.fit_width_container.show()
            self.output_label.show()

        elif mode == ResizeMode.FIT_TO_HEIGHT:
            self.original_label.show()
            self.fit_height_container.show()
            self.output_label.show()

        elif mode == ResizeMode.FIT_TO_DIMENSIONS:
            self.original_label.show()
            self.dimensions_container.show()
            self.output_label.show()

        self._update_output_dimensions()
        self.settings_changed.emit()

    def _on_percentage_changed(self, value: int):
        """Handle percentage slider change."""
        self.percentage_value_label.setText(f"{value}%")
        self._update_output_dimensions()
        self.settings_changed.emit()

    def _on_target_changed(self):
        """Handle target width/height or upscaling change."""
        self._update_output_dimensions()
        self.settings_changed.emit()

    def _on_dimensions_changed(self):
        """Handle max width/height or upscaling change."""
        self._update_output_dimensions()
        self.settings_changed.emit()

    def _update_output_dimensions(self):
        """Calculate and display output dimensions."""
        if not self.current_image_width or not self.current_image_height:
            self.output_label.setText("Output: —")
            return

        mode = self.resize_mode_combo.currentData()

        if mode == ResizeMode.NONE:
            return

        elif mode == ResizeMode.PERCENTAGE:
            scale = self.percentage_slider.value() / 100.0
            output_w = int(self.current_image_width * scale)
            output_h = int(self.current_image_height * scale)
            self.output_label.setText(f"Output: {output_w} × {output_h} px")

        elif mode == ResizeMode.FIT_TO_WIDTH:
            target_w = self.target_width_spinbox.value()
            allow_upscale = self.fit_width_upscale_checkbox.isChecked()

            aspect_ratio = self.current_image_width / self.current_image_height
            output_w = target_w
            output_h = int(target_w / aspect_ratio)

            if not allow_upscale and output_w > self.current_image_width:
                output_w = self.current_image_width
                output_h = self.current_image_height

            self.output_label.setText(f"Output: {output_w} × {output_h} px")

        elif mode == ResizeMode.FIT_TO_HEIGHT:
            target_h = self.target_height_spinbox.value()
            allow_upscale = self.fit_height_upscale_checkbox.isChecked()

            aspect_ratio = self.current_image_width / self.current_image_height
            output_h = target_h
            output_w = int(target_h * aspect_ratio)

            if not allow_upscale and output_h > self.current_image_height:
                output_w = self.current_image_width
                output_h = self.current_image_height

            self.output_label.setText(f"Output: {output_w} × {output_h} px")

        elif mode == ResizeMode.FIT_TO_DIMENSIONS:
            max_w = self.max_width_spinbox.value()
            max_h = self.max_height_spinbox.value()
            allow_upscale = self.dimensions_upscale_checkbox.isChecked()

            new_w, new_h = self._calculate_fit_dimensions(
                self.current_image_width, self.current_image_height,
                max_w, max_h, allow_upscale
            )

            self.output_label.setText(f"Output: {new_w} × {new_h} px")

    def _calculate_fit_dimensions(self, orig_w, orig_h, max_w, max_h, allow_upscale):
        """Calculate dimensions for Fit to Dimensions mode."""
        aspect_ratio = orig_w / orig_h

        if orig_w / max_w > orig_h / max_h:
            new_w = max_w
            new_h = int(max_w / aspect_ratio)
        else:
            new_h = max_h
            new_w = int(max_h * aspect_ratio)

        if not allow_upscale:
            new_w = min(new_w, orig_w)
            new_h = min(new_h, orig_h)

        return new_w, new_h

    def get_settings(self) -> dict:
        """Get current resize settings."""
        mode = self.resize_mode_combo.currentData()

        return {
            "resize_mode": mode,
            "resize_percentage": self.percentage_slider.value(),
            "target_width_px": self.target_width_spinbox.value() if mode == ResizeMode.FIT_TO_WIDTH else None,
            "target_height_px": self.target_height_spinbox.value() if mode == ResizeMode.FIT_TO_HEIGHT else None,
            "max_width_px": self.max_width_spinbox.value() if mode == ResizeMode.FIT_TO_DIMENSIONS else None,
            "max_height_px": self.max_height_spinbox.value() if mode == ResizeMode.FIT_TO_DIMENSIONS else None,
            "allow_upscaling": (
                self.fit_width_upscale_checkbox.isChecked() if mode == ResizeMode.FIT_TO_WIDTH else
                self.fit_height_upscale_checkbox.isChecked() if mode == ResizeMode.FIT_TO_HEIGHT else
                self.dimensions_upscale_checkbox.isChecked() if mode == ResizeMode.FIT_TO_DIMENSIONS else
                False
            ),
        }

    def set_current_image(self, width: int, height: int):
        """Update with current image dimensions."""
        self.current_image_width = width
        self.current_image_height = height

        if width and height:
            self.original_label.setText(f"Original: {width} × {height} px")
        else:
            self.original_label.setText("Original: —")

        self._update_output_dimensions()

    def clear_current_image(self):
        """Clear current image dimensions."""
        self.current_image_width = None
        self.current_image_height = None
        self.original_label.setText("Original: —")
        self._update_output_dimensions()
