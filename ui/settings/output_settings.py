"""
Output settings widget for image conversion.

Handles format selection, quality/target size modes, and output folder.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QCheckBox, QRadioButton, QLineEdit, QSpinBox,
    QPushButton, QFileDialog, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
from core.format_settings import ImageFormat


class OutputSettingsWidget(QWidget):
    """Widget for output-related settings."""

    settings_changed = Signal()
    format_changed = Signal(ImageFormat)  # Emitted when format changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_folder = Path(Path.home() / "Downloads" / "Converted")
        self._setup_ui()

    def _setup_ui(self):
        """Build the output settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        for fmt in ImageFormat:
            self.format_combo.addItem(fmt.value, fmt)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo, 1)
        layout.addLayout(format_layout)

        # Compression mode
        self.mode_quality = QRadioButton("Quality-based")
        self.mode_quality.setChecked(True)
        self.mode_quality.toggled.connect(self._on_mode_changed)
        self.mode_target = QRadioButton("Target file size")
        self.mode_target.toggled.connect(self._on_mode_changed)
        layout.addWidget(self.mode_quality)
        layout.addWidget(self.mode_target)

        # Quality slider
        self.quality_container = QWidget()
        quality_layout = QVBoxLayout(self.quality_container)
        quality_layout.setContentsMargins(0, 0, 0, 0)
        quality_layout.setSpacing(4)

        quality_label_layout = QHBoxLayout()
        quality_label_layout.addWidget(QLabel("Quality:"))
        self.quality_value_label = QLabel("85")
        self.quality_value_label.setProperty("class", "value-label")
        quality_label_layout.addWidget(self.quality_value_label)
        quality_label_layout.addStretch()
        quality_layout.addLayout(quality_label_layout)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)
        quality_layout.addWidget(self.quality_slider)
        layout.addWidget(self.quality_container)

        # Target size
        self.target_container = QWidget()
        target_layout = QHBoxLayout(self.target_container)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(6)
        target_layout.addWidget(QLabel("Target:"))
        self.target_size_input = QLineEdit()
        self.target_size_input.setObjectName("target-size-input")
        self.target_size_input.setPlaceholderText("500")
        self.target_size_input.textChanged.connect(self.settings_changed.emit)
        self.target_unit_combo = QComboBox()
        self.target_unit_combo.setObjectName("target-unit-combo")
        self.target_unit_combo.addItems(["KB", "MB"])
        self.target_unit_combo.currentIndexChanged.connect(self.settings_changed.emit)
        target_layout.addWidget(self.target_size_input)
        target_layout.addWidget(self.target_unit_combo)
        target_layout.addStretch()
        layout.addWidget(self.target_container)
        self.target_container.hide()

        # PNG compress level
        self.png_container = QWidget()
        png_layout = QVBoxLayout(self.png_container)
        png_layout.setContentsMargins(0, 0, 0, 0)
        png_layout.setSpacing(4)

        png_label_layout = QHBoxLayout()
        png_label_layout.addWidget(QLabel("Level:"))
        self.png_level_spin = QSpinBox()
        self.png_level_spin.setMinimum(0)
        self.png_level_spin.setMaximum(9)
        self.png_level_spin.setValue(6)
        self.png_level_spin.valueChanged.connect(self.settings_changed.emit)
        png_label_layout.addWidget(self.png_level_spin)
        png_label_layout.addStretch()
        png_layout.addLayout(png_label_layout)

        png_note = QLabel("0=Fast, 9=Smallest")
        png_note.setProperty("class", "info-note")
        png_layout.addWidget(png_note)
        layout.addWidget(self.png_container)
        self.png_container.hide()

        # Checkboxes
        self.lossless_check = QCheckBox("Lossless")
        self.lossless_check.stateChanged.connect(self._on_lossless_changed)
        layout.addWidget(self.lossless_check)

        self.metadata_check = QCheckBox("Keep metadata")
        self.metadata_check.setChecked(True)
        self.metadata_check.stateChanged.connect(self.settings_changed.emit)
        layout.addWidget(self.metadata_check)

    def _on_format_changed(self):
        """Handle format change."""
        format_enum = self.format_combo.currentData()

        if format_enum == ImageFormat.PNG:
            self.mode_quality.hide()
            self.mode_target.hide()
            self.quality_container.hide()
            self.target_container.hide()
            self.png_container.show()
            self.lossless_check.hide()
        else:
            self.mode_quality.show()
            self.mode_target.show()
            self.png_container.hide()
            self._on_mode_changed()

            if format_enum == ImageFormat.JPEG:
                self.lossless_check.hide()
            else:  # WebP or AVIF
                self.lossless_check.show()

        self.format_changed.emit(format_enum)
        self.settings_changed.emit()

    def _on_mode_changed(self):
        """Handle compression mode change."""
        if self.mode_quality.isChecked():
            self.quality_container.show()
            self.target_container.hide()
        else:
            self.quality_container.hide()
            self.target_container.show()
        self.settings_changed.emit()

    def _on_lossless_changed(self):
        """Handle lossless checkbox change."""
        is_lossless = self.lossless_check.isChecked()
        self.quality_slider.setEnabled(not is_lossless)
        self.quality_value_label.setEnabled(not is_lossless)
        self.settings_changed.emit()

    def _on_quality_changed(self, value: int):
        """Handle quality slider change."""
        self.quality_value_label.setText(str(value))
        self.settings_changed.emit()

    def get_settings(self) -> dict:
        """Get current output settings as a dictionary."""
        settings = {
            'output_format': self.format_combo.currentData(),
            'quality': self.quality_slider.value(),
            'lossless': self.lossless_check.isChecked() if self.lossless_check.isVisible() else False,
            'keep_metadata': self.metadata_check.isChecked(),
            'png_compress_level': self.png_level_spin.value(),
            'target_size_kb': None
        }

        # Handle target size
        if self.mode_target.isChecked() and self.target_size_input.text():
            try:
                size_value = float(self.target_size_input.text())
                if self.target_unit_combo.currentText() == "MB":
                    size_value *= 1024
                settings['target_size_kb'] = size_value
            except ValueError:
                pass

        return settings

    def get_selected_format(self) -> ImageFormat:
        """Get currently selected format."""
        return self.format_combo.currentData()
