from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSlider, QCheckBox, QGroupBox, QPushButton,
    QFileDialog, QSpinBox, QRadioButton, QButtonGroup, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
from core.format_settings import ImageFormat, ConversionSettings


class SettingsPanel(QWidget):
    """Panel for conversion settings with advanced options."""

    settings_changed = Signal(ConversionSettings)
    convert_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_folder: Path = Path.home() / "Downloads" / "Converted"
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Convert button at top
        self.convert_btn = QPushButton("▶ Convert Selected")
        self.convert_btn.setStyleSheet(
            "min-height: 36px; font-size: 11pt; font-weight: bold;"
        )
        self.convert_btn.clicked.connect(self.convert_requested.emit)
        self.convert_btn.setEnabled(False)
        layout.addWidget(self.convert_btn)

        # Settings group box
        settings_group = QGroupBox("Output Settings")
        settings_layout = QVBoxLayout(settings_group)

        # Format selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        format_label.setMinimumWidth(80)

        self.format_combo = QComboBox()
        for fmt in ImageFormat:
            self.format_combo.addItem(fmt.value, fmt)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)

        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        settings_layout.addLayout(format_layout)

        # Compression mode selection
        mode_layout = QVBoxLayout()
        mode_layout.addWidget(QLabel("Compression Mode:"))

        self.mode_quality = QRadioButton("Quality-based")
        self.mode_quality.setChecked(True)
        self.mode_quality.toggled.connect(self._on_mode_changed)

        self.mode_target = QRadioButton("Target file size")
        self.mode_target.toggled.connect(self._on_mode_changed)

        mode_layout.addWidget(self.mode_quality)
        mode_layout.addWidget(self.mode_target)
        settings_layout.addLayout(mode_layout)

        # Quality slider container
        self.quality_container = QWidget()
        quality_layout = QVBoxLayout(self.quality_container)
        quality_layout.setContentsMargins(0, 0, 0, 0)

        quality_label_layout = QHBoxLayout()
        quality_label_layout.addWidget(QLabel("Quality:"))

        self.quality_value_label = QLabel("85")
        self.quality_value_label.setStyleSheet("color: #007acc; font-weight: bold;")
        quality_label_layout.addWidget(self.quality_value_label)
        quality_label_layout.addStretch()

        quality_layout.addLayout(quality_label_layout)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)

        quality_layout.addWidget(self.quality_slider)
        settings_layout.addWidget(self.quality_container)

        # Target size container
        self.target_container = QWidget()
        target_layout = QHBoxLayout(self.target_container)
        target_layout.setContentsMargins(0, 0, 0, 0)

        target_layout.addWidget(QLabel("Target size:"))

        self.target_size_input = QLineEdit()
        self.target_size_input.setPlaceholderText("e.g., 500")
        self.target_size_input.setMaximumWidth(80)
        self.target_size_input.textChanged.connect(self._on_settings_changed)

        self.target_unit_combo = QComboBox()
        self.target_unit_combo.addItems(["KB", "MB"])
        self.target_unit_combo.currentIndexChanged.connect(self._on_settings_changed)

        target_layout.addWidget(self.target_size_input)
        target_layout.addWidget(self.target_unit_combo)
        target_layout.addStretch()

        settings_layout.addWidget(self.target_container)
        self.target_container.hide()  # Hidden by default

        # PNG compress level (0-9)
        self.png_container = QWidget()
        png_layout = QVBoxLayout(self.png_container)
        png_layout.setContentsMargins(0, 0, 0, 0)

        png_label_layout = QHBoxLayout()
        png_label_layout.addWidget(QLabel("Compression Level:"))

        self.png_level_spin = QSpinBox()
        self.png_level_spin.setMinimum(0)
        self.png_level_spin.setMaximum(9)
        self.png_level_spin.setValue(6)
        self.png_level_spin.setToolTip("0 = Fast/Large, 9 = Slow/Small")
        self.png_level_spin.valueChanged.connect(self._on_settings_changed)

        png_label_layout.addWidget(self.png_level_spin)
        png_label_layout.addStretch()

        png_layout.addLayout(png_label_layout)

        png_note = QLabel("PNG is always lossless.\nHigher = smaller file, slower encoding.")
        png_note.setStyleSheet("color: #808080; font-size: 9pt;")
        png_note.setWordWrap(True)
        png_layout.addWidget(png_note)

        settings_layout.addWidget(self.png_container)
        self.png_container.hide()

        # Lossless checkbox (WebP, AVIF)
        self.lossless_check = QCheckBox("Lossless compression (ignores quality)")
        self.lossless_check.stateChanged.connect(self._on_lossless_changed)
        settings_layout.addWidget(self.lossless_check)

        # Advanced options (collapsible)
        self.advanced_check = QCheckBox("Show advanced options")
        self.advanced_check.stateChanged.connect(self._on_advanced_toggled)
        settings_layout.addWidget(self.advanced_check)

        # Advanced container
        self.advanced_container = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_container)
        advanced_layout.setContentsMargins(0, 0, 0, 0)

        # WebP method
        self.webp_method_layout = QHBoxLayout()
        self.webp_method_layout.addWidget(QLabel("Method (0-6):"))
        self.webp_method_spin = QSpinBox()
        self.webp_method_spin.setMinimum(0)
        self.webp_method_spin.setMaximum(6)
        self.webp_method_spin.setValue(6)
        self.webp_method_spin.setToolTip("Compression effort: 0=Fast, 6=Best")
        self.webp_method_spin.valueChanged.connect(self._on_settings_changed)
        self.webp_method_layout.addWidget(self.webp_method_spin)
        self.webp_method_layout.addStretch()

        webp_method_widget = QWidget()
        webp_method_widget.setLayout(self.webp_method_layout)
        advanced_layout.addWidget(webp_method_widget)

        # AVIF speed
        self.avif_speed_layout = QHBoxLayout()
        self.avif_speed_layout.addWidget(QLabel("Speed (0-10):"))
        self.avif_speed_spin = QSpinBox()
        self.avif_speed_spin.setMinimum(0)
        self.avif_speed_spin.setMaximum(10)
        self.avif_speed_spin.setValue(4)
        self.avif_speed_spin.setToolTip("Encoding speed: 0=Slowest/Best, 10=Fastest")
        self.avif_speed_spin.valueChanged.connect(self._on_settings_changed)
        self.avif_speed_layout.addWidget(self.avif_speed_spin)
        self.avif_speed_layout.addStretch()

        avif_speed_widget = QWidget()
        avif_speed_widget.setLayout(self.avif_speed_layout)
        advanced_layout.addWidget(avif_speed_widget)

        settings_layout.addWidget(self.advanced_container)
        self.advanced_container.hide()

        # Keep metadata checkbox
        self.metadata_check = QCheckBox("Keep image metadata (EXIF)")
        self.metadata_check.setChecked(True)
        self.metadata_check.stateChanged.connect(self._on_settings_changed)
        settings_layout.addWidget(self.metadata_check)

        layout.addWidget(settings_group)

        # Output folder selection
        folder_group = QGroupBox("Output Folder")
        folder_layout = QVBoxLayout(folder_group)

        folder_select_layout = QHBoxLayout()

        self.folder_label = QLabel(str(self.output_folder))
        self.folder_label.setStyleSheet(
            "padding: 6px; background-color: #252526; "
            "border: 1px solid #3e3e42; border-radius: 4px;"
        )
        self.folder_label.setWordWrap(True)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_output_folder)

        folder_select_layout.addWidget(self.folder_label, stretch=1)
        folder_select_layout.addWidget(self.browse_btn)

        folder_layout.addLayout(folder_select_layout)
        layout.addWidget(folder_group)

        layout.addStretch()

        self._on_format_changed()

    def _on_mode_changed(self):
        """Handle compression mode change."""
        if self.mode_quality.isChecked():
            self.quality_container.show()
            self.target_container.hide()
        else:
            self.quality_container.hide()
            self.target_container.show()

        self._on_settings_changed()

    def _on_advanced_toggled(self):
        """Toggle advanced options visibility."""
        self.advanced_container.setVisible(self.advanced_check.isChecked())

    def _on_format_changed(self):
        """Handle format change - show/hide appropriate controls."""
        format_enum = self.format_combo.currentData()

        # Hide mode selection for PNG
        if format_enum == ImageFormat.PNG:
            self.mode_quality.hide()
            self.mode_target.hide()
            self.quality_container.hide()
            self.target_container.hide()
            self.png_container.show()
            self.lossless_check.hide()
            self.advanced_check.hide()
            self.advanced_container.hide()
        else:
            self.mode_quality.show()
            self.mode_target.show()
            self.png_container.hide()
            self._on_mode_changed()

            if format_enum == ImageFormat.JPEG:
                self.lossless_check.hide()
                self.advanced_check.hide()
                self.advanced_container.hide()
            else:  # WebP, AVIF
                self.lossless_check.show()
                self.advanced_check.show()

        # Show/hide format-specific advanced options
        if self.advanced_check.isChecked():
            for i in range(self.advanced_container.layout().count()):
                widget = self.advanced_container.layout().itemAt(i).widget()
                if widget:
                    if "Method" in widget.layout().itemAt(0).widget().text():
                        widget.setVisible(format_enum == ImageFormat.WEBP)
                    elif "Speed" in widget.layout().itemAt(0).widget().text():
                        widget.setVisible(format_enum == ImageFormat.AVIF)

        self._on_settings_changed()

    def _on_lossless_changed(self):
        """Handle lossless checkbox change."""
        is_lossless = self.lossless_check.isChecked()
        self.quality_slider.setEnabled(not is_lossless)
        self.quality_value_label.setEnabled(not is_lossless)
        self._on_settings_changed()

    def _on_quality_changed(self, value: int):
        """Handle quality slider change."""
        self.quality_value_label.setText(str(value))
        self._on_settings_changed()

    def _on_settings_changed(self):
        """Emit settings changed signal."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)

    def _browse_output_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(self.output_folder)
        )

        if folder:
            self.output_folder = Path(folder)
            self.folder_label.setText(str(self.output_folder))

    def get_settings(self) -> ConversionSettings:
        """Get current conversion settings."""
        format_enum = self.format_combo.currentData()

        settings = ConversionSettings(
            output_format=format_enum,
            quality=self.quality_slider.value(),
            lossless=self.lossless_check.isChecked() if self.lossless_check.isVisible() else False,
            keep_metadata=self.metadata_check.isChecked()
        )

        # PNG-specific
        if format_enum == ImageFormat.PNG:
            settings.png_compress_level = self.png_level_spin.value()

        # Target size mode
        if self.mode_target.isChecked() and self.target_size_input.text():
            try:
                size_value = float(self.target_size_input.text())
                if self.target_unit_combo.currentText() == "MB":
                    size_value *= 1024
                settings.target_size_kb = size_value
            except ValueError:
                pass

        # Advanced options
        if self.advanced_check.isChecked():
            if format_enum == ImageFormat.WEBP:
                settings.webp_method = self.webp_method_spin.value()
            elif format_enum == ImageFormat.AVIF:
                settings.avif_speed = self.avif_speed_spin.value()

        return settings

    def get_output_folder(self) -> Path:
        """Get selected output folder."""
        return self.output_folder

    def set_convert_enabled(self, enabled: bool):
        """Enable/disable convert button."""
        self.convert_btn.setEnabled(enabled)
