"""
Output settings widget for image conversion.

Handles format selection, quality/target size modes, output folder, and filename templates.
"""
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QCheckBox, QRadioButton, QLineEdit, QSpinBox,
    QPushButton, QFileDialog, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
from core.format_settings import ImageFormat, OutputLocationMode, FilenameTemplate


class OutputSettingsWidget(QWidget):
    """Widget for output-related settings."""

    settings_changed = Signal()
    format_changed = Signal(ImageFormat)  # Emitted when format changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_size_bytes: int | None = None
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

        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
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
        self.target_size_input.textChanged.connect(lambda: self.settings_changed.emit())
        self.target_unit_combo = QComboBox()
        self.target_unit_combo.setObjectName("target-unit-combo")
        self.target_unit_combo.addItems(["KB", "MB"])
        self.target_unit_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())
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
        self.png_level_spin.valueChanged.connect(lambda: self.settings_changed.emit())
        png_label_layout.addWidget(self.png_level_spin)
        png_label_layout.addStretch()
        png_layout.addLayout(png_label_layout)

        png_note = QLabel("0=Fast, 9=Smallest")
        png_note.setProperty("class", "info-note")
        png_layout.addWidget(png_note)
        layout.addWidget(self.png_container)
        self.png_container.hide()

        # ==========================================
        # TIFF CONTAINER
        # ==========================================
        self.tiff_container = QWidget()
        tiff_layout = QVBoxLayout(self.tiff_container)
        tiff_layout.setContentsMargins(0, 0, 0, 0)
        tiff_layout.setSpacing(4)

        tiff_label_layout = QHBoxLayout()
        tiff_label_layout.addWidget(QLabel("Compression:"))
        self.tiff_compression_combo = QComboBox()
        self.tiff_compression_combo.addItem("None", "none")
        self.tiff_compression_combo.addItem("LZW (Lossless)", "lzw")
        self.tiff_compression_combo.addItem("JPEG (Lossy)", "jpeg")
        self.tiff_compression_combo.addItem("PackBits", "packbits")
        self.tiff_compression_combo.setCurrentIndex(1)  # Default: LZW
        self.tiff_compression_combo.currentIndexChanged.connect(self._on_tiff_compression_changed)
        tiff_label_layout.addWidget(self.tiff_compression_combo, 1)
        tiff_layout.addLayout(tiff_label_layout)

        # TIFF JPEG quality (only shown when JPEG compression selected)
        self.tiff_jpeg_quality_container = QWidget()
        tiff_jpeg_layout = QVBoxLayout(self.tiff_jpeg_quality_container)
        tiff_jpeg_layout.setContentsMargins(0, 0, 0, 0)
        tiff_jpeg_layout.setSpacing(4)

        tiff_jpeg_label_layout = QHBoxLayout()
        tiff_jpeg_label_layout.addWidget(QLabel("JPEG Quality:"))
        self.tiff_jpeg_quality_label = QLabel("85")
        self.tiff_jpeg_quality_label.setProperty("class", "value-label")
        tiff_jpeg_label_layout.addWidget(self.tiff_jpeg_quality_label)
        tiff_jpeg_label_layout.addStretch()
        tiff_jpeg_layout.addLayout(tiff_jpeg_label_layout)

        self.tiff_jpeg_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.tiff_jpeg_quality_slider.setMinimum(1)
        self.tiff_jpeg_quality_slider.setMaximum(100)
        self.tiff_jpeg_quality_slider.setValue(85)
        self.tiff_jpeg_quality_slider.valueChanged.connect(self._on_tiff_jpeg_quality_changed)
        tiff_jpeg_layout.addWidget(self.tiff_jpeg_quality_slider)
        tiff_layout.addWidget(self.tiff_jpeg_quality_container)
        self.tiff_jpeg_quality_container.hide()  # Hidden by default

        tiff_note = QLabel("LZW: Best for lossless compression")
        tiff_note.setProperty("class", "info-note")
        tiff_layout.addWidget(tiff_note)
        layout.addWidget(self.tiff_container)
        self.tiff_container.hide()

        # ==========================================
        # GIF CONTAINER
        # ==========================================
        self.gif_container = QWidget()
        gif_layout = QVBoxLayout(self.gif_container)
        gif_layout.setContentsMargins(0, 0, 0, 0)
        gif_layout.setSpacing(4)

        self.gif_optimize_check = QCheckBox("Optimize palette")
        self.gif_optimize_check.setChecked(True)
        self.gif_optimize_check.setToolTip("Reduce file size by optimizing color palette")
        self.gif_optimize_check.stateChanged.connect(lambda: self.settings_changed.emit())
        gif_layout.addWidget(self.gif_optimize_check)

        gif_warning = QLabel("⚠️ GIF limited to 256 colors (may show dithering)")
        gif_warning.setProperty("class", "info-note")
        gif_warning.setWordWrap(True)
        gif_layout.addWidget(gif_warning)
        layout.addWidget(self.gif_container)
        self.gif_container.hide()

        # ==========================================
        # ICO CONTAINER
        # ==========================================
        self.ico_container = QWidget()
        ico_layout = QVBoxLayout(self.ico_container)
        ico_layout.setContentsMargins(0, 0, 0, 0)
        ico_layout.setSpacing(6)

        # Size spinbox
        ico_size_layout = QHBoxLayout()
        ico_size_layout.addWidget(QLabel("Icon Size:"))
        self.ico_size_spinbox = QSpinBox()
        self.ico_size_spinbox.setRange(16, 256)
        self.ico_size_spinbox.setSingleStep(16)
        self.ico_size_spinbox.setValue(256)
        self.ico_size_spinbox.setSuffix(" px")
        self.ico_size_spinbox.setToolTip("Square dimensions (16-256 pixels, PIL limitation)")
        self.ico_size_spinbox.valueChanged.connect(lambda: self.settings_changed.emit())
        ico_size_layout.addWidget(self.ico_size_spinbox)
        ico_size_layout.addStretch()
        ico_layout.addLayout(ico_size_layout)

        # Force square method
        ico_layout.addWidget(QLabel("If not square:"))
        self.ico_force_square_pad = QRadioButton("Pad with transparency")
        self.ico_force_square_pad.setChecked(True)
        self.ico_force_square_pad.setToolTip("Add transparent borders to preserve entire image")
        self.ico_force_square_pad.toggled.connect(lambda: self.settings_changed.emit())
        ico_layout.addWidget(self.ico_force_square_pad)

        self.ico_force_square_crop = QRadioButton("Crop to center")
        self.ico_force_square_crop.setToolTip("Zoom-fill and crop edges to fit square")
        self.ico_force_square_crop.toggled.connect(lambda: self.settings_changed.emit())
        ico_layout.addWidget(self.ico_force_square_crop)

        ico_note = QLabel("ICO files are always square")
        ico_note.setProperty("class", "info-note")
        ico_layout.addWidget(ico_note)
        layout.addWidget(self.ico_container)
        self.ico_container.hide()

        # ==========================================
        # BMP CONTAINER
        # ==========================================
        self.bmp_container = QWidget()
        bmp_layout = QVBoxLayout(self.bmp_container)
        bmp_layout.setContentsMargins(0, 0, 0, 0)
        bmp_layout.setSpacing(4)

        bmp_info = QLabel("BMP is uncompressed (no quality options)")
        bmp_info.setProperty("class", "info-note")
        bmp_info.setWordWrap(True)
        bmp_layout.addWidget(bmp_info)
        layout.addWidget(self.bmp_container)
        self.bmp_container.hide()

        # Checkboxes
        self.lossless_check = QCheckBox("Lossless")
        self.lossless_check.stateChanged.connect(self._on_lossless_changed)
        layout.addWidget(self.lossless_check)

        self.metadata_check = QCheckBox("Keep metadata")
        self.metadata_check.setChecked(True)
        self.metadata_check.stateChanged.connect(lambda: self.settings_changed.emit())
        layout.addWidget(self.metadata_check)

        # Estimated File Size Display
        self.estimated_size_label = QLabel("Est. Size: —")
        self.estimated_size_label.setToolTip("Show estimated file size based on current settings. Actual size may differ after conversion.")
        self.estimated_size_label.setAlignment(QtCore.Qt.AlignCenter)
        self.estimated_size_label.setObjectName("estimated-size-label")
        layout.addWidget(self.estimated_size_label)

        # ========== OUTPUT LOCATION SECTION ==========
        location_group = QGroupBox("Output Location")
        location_group.setObjectName("OutputLocation")
        location_layout = QVBoxLayout(location_group)
        location_layout.setSpacing(6)

        # Same as source option (first)
        self.output_mode_source = QRadioButton("Same as Source")
        self.output_mode_source.setToolTip("Save converted files next to original files")
        self.output_mode_source.toggled.connect(self._on_output_mode_changed)
        location_layout.addWidget(self.output_mode_source)

        # Ask every time option (second)
        self.output_mode_ask = QRadioButton("Ask Every Time")
        self.output_mode_ask.setToolTip("Choose output folder before each conversion")
        self.output_mode_ask.toggled.connect(self._on_output_mode_changed)
        location_layout.addWidget(self.output_mode_ask)

        # Custom folder option (third)
        self.output_mode_custom = QRadioButton("Custom Folder")
        self.output_mode_custom.setChecked(True)
        self.output_mode_custom.toggled.connect(self._on_output_mode_changed)
        location_layout.addWidget(self.output_mode_custom)

        # Custom folder path + browse button (immediately below Custom Folder radio)
        folder_layout = QHBoxLayout()
        folder_layout.setContentsMargins(20, 0, 0, 0)
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setText(str(self.output_folder))
        self.output_folder_edit.setReadOnly(True)
        self.output_folder_browse_btn = QPushButton("Browse")
        self.output_folder_browse_btn.clicked.connect(self.browse_output_folder)
        folder_layout.addWidget(self.output_folder_edit, 1)
        folder_layout.addWidget(self.output_folder_browse_btn)
        location_layout.addLayout(folder_layout)

        layout.addWidget(location_group)

        # ========== FILENAME PATTERN SECTION ==========
        filename_group = QGroupBox("Filename Pattern")
        filename_group.setObjectName("FilenamePattern")
        filename_layout = QVBoxLayout(filename_group)
        filename_layout.setSpacing(6)

        # ===== Base filename controls =====
        self.base_name_original = QRadioButton("Use Original Filename")
        self.base_name_original.setChecked(True)
        self.base_name_original.setToolTip("Keep source image filename (default)")
        filename_layout.addWidget(self.base_name_original)

        # Custom rename option
        rename_layout = QHBoxLayout()
        self.base_name_custom = QRadioButton("Rename to:")
        self.base_name_custom.setToolTip("Replace base filename for batch conversion")
        self.base_name_custom.toggled.connect(self._on_base_name_mode_changed)
        rename_layout.addWidget(self.base_name_custom)

        self.base_name_input = QLineEdit()
        self.base_name_input.setPlaceholderText("e.g., website-photo, product-image")
        self.base_name_input.setEnabled(False)
        self.base_name_input.textChanged.connect(lambda: self.settings_changed.emit())
        rename_layout.addWidget(self.base_name_input, 1)
        filename_layout.addLayout(rename_layout)

        # Visual separator
        filename_layout.addSpacing(8)

        # Enable suffix checkbox
        self.enable_suffix_check = QCheckBox("Enable filename suffix")
        self.enable_suffix_check.setChecked(True)  # Default ON
        self.enable_suffix_check.setToolTip("Toggle adding suffix to converted filenames")
        filename_layout.addWidget(self.enable_suffix_check)

        # React to toggle: gray out pattern controls when disabled
        self.enable_suffix_check.stateChanged.connect(lambda: self._on_enable_suffix_toggled())
        self.enable_suffix_check.stateChanged.connect(lambda: self.settings_changed.emit())

        # Template dropdown
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Suffix:"))
        self.filename_template_combo = QComboBox()
        self.filename_template_combo.addItem("_converted", FilenameTemplate.CONVERTED)
        self.filename_template_combo.addItem("_[format]", FilenameTemplate.FORMAT)
        self.filename_template_combo.addItem("_Q[quality]", FilenameTemplate.QUALITY)
        self.filename_template_combo.addItem("Custom...", FilenameTemplate.CUSTOM)
        self.filename_template_combo.currentIndexChanged.connect(self._on_template_changed)

        template_layout.addWidget(self.filename_template_combo, 1)
        filename_layout.addLayout(template_layout)

        # Custom suffix input field (hidden by default)
        self.custom_suffix_container = QWidget()
        custom_suffix_layout = QHBoxLayout(self.custom_suffix_container)
        custom_suffix_layout.setContentsMargins(0, 0, 0, 0)
        custom_suffix_layout.setSpacing(6)
        custom_suffix_layout.addWidget(QLabel("Custom:"))
        self.custom_suffix_input = QLineEdit()
        self.custom_suffix_input.setPlaceholderText("e.g., _optimized or _final")
        self.custom_suffix_input.setToolTip("Enter custom suffix (underscore is optional)")
        self.custom_suffix_input.textChanged.connect(lambda: self.settings_changed.emit())
        custom_suffix_layout.addWidget(self.custom_suffix_input, 1)
        filename_layout.addWidget(self.custom_suffix_container)
        self.custom_suffix_container.hide()  # Hidden by default

        # Auto-increment checkbox
        self.auto_increment_check = QCheckBox("Auto-increment if file exists")
        self.auto_increment_check.setChecked(True)
        self.auto_increment_check.setToolTip("Append _1, _2, _3... if filename already exists")
        self.auto_increment_check.stateChanged.connect(lambda: self.settings_changed.emit())
        filename_layout.addWidget(self.auto_increment_check)

        # Add the group to the main layout
        layout.addWidget(filename_group)

    def _on_format_changed(self):
        """Handle format change."""
        format_enum = self.format_combo.currentData()

        # Hide ALL format-specific containers first
        self.quality_container.hide()
        self.png_container.hide()
        self.tiff_container.hide()
        self.gif_container.hide()
        self.ico_container.hide()
        self.bmp_container.hide()
        self.target_container.hide()

        # Handle format-specific UI visibility
        if format_enum == ImageFormat.PNG:
            self.mode_quality.hide()
            self.mode_target.hide()
            self.png_container.show()
            self.lossless_check.hide()

        elif format_enum == ImageFormat.TIFF:
            self.mode_quality.hide()
            self.mode_target.hide()
            self.tiff_container.show()
            self.lossless_check.hide()

        elif format_enum == ImageFormat.GIF:
            self.mode_quality.hide()
            self.mode_target.hide()
            self.gif_container.show()
            self.lossless_check.hide()

        elif format_enum == ImageFormat.ICO:
            self.mode_quality.hide()
            self.mode_target.hide()
            self.ico_container.show()
            self.lossless_check.hide()

        elif format_enum == ImageFormat.BMP:
            self.mode_quality.hide()
            self.mode_target.hide()
            self.bmp_container.show()
            self.lossless_check.hide()

        else:  # JPEG, WebP, AVIF
            self.mode_quality.show()
            self.mode_target.show()
            self._on_mode_changed()  # Show quality or target container

            if format_enum == ImageFormat.JPEG:
                self.lossless_check.hide()
            else:  # WebP or AVIF
                self.lossless_check.show()

        self.format_changed.emit(format_enum)
        self.settings_changed.emit()

    def _on_tiff_compression_changed(self):
        """Handle TIFF compression type change."""
        compression = self.tiff_compression_combo.currentData()

        # Show JPEG quality slider only when JPEG compression is selected
        if compression == "jpeg":
            self.tiff_jpeg_quality_container.show()
        else:
            self.tiff_jpeg_quality_container.hide()

        self.settings_changed.emit()

    def _on_tiff_jpeg_quality_changed(self, value: int):
        """Handle TIFF JPEG quality slider change."""
        self.tiff_jpeg_quality_label.setText(str(value))
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

    def _on_output_mode_changed(self):
        """Handle output location mode change."""
        # Enable/disable folder controls based on mode
        is_custom_mode = self.output_mode_custom.isChecked()
        self.output_folder_edit.setEnabled(is_custom_mode)
        self.output_folder_browse_btn.setEnabled(is_custom_mode)
        self.settings_changed.emit()

    def _on_template_changed(self):
        """Handle template dropdown change - show/hide custom input."""
        current_template = self.filename_template_combo.currentData()

        # Show custom input only when CUSTOM is selected
        if current_template == FilenameTemplate.CUSTOM:
            self.custom_suffix_container.show()
        else:
            self.custom_suffix_container.hide()

        self.settings_changed.emit()

    def _on_base_name_mode_changed(self):
        """Handle base name mode toggle - enable/disable text input."""
        is_custom = self.base_name_custom.isChecked()
        self.base_name_input.setEnabled(is_custom)
        self.settings_changed.emit()

    def browse_output_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(self.output_folder)
        )
        if folder:
            self.output_folder = Path(folder)
            self.output_folder_edit.setText(str(self.output_folder))
            self.settings_changed.emit()

    def get_settings(self) -> dict:
        """Get current output settings as a dictionary."""
        settings = {
            'output_format': self.format_combo.currentData(),
            'quality': self.quality_slider.value(),
            'lossless': self.lossless_check.isChecked() if self.lossless_check.isVisible() else False,
            'keep_metadata': self.metadata_check.isChecked(),
            'png_compress_level': self.png_level_spin.value(),
            'target_size_kb': None,
            # OUTPUT FIELDS
            'output_location_mode': self._get_output_mode(),
            'custom_output_folder': self.output_folder,
            'filename_template': self.filename_template_combo.currentData(),
            'custom_suffix': self.custom_suffix_input.text().strip(),
            'custom_base_name': self.base_name_input.text().strip() if self.base_name_custom.isChecked() else "",
            'auto_increment': self.auto_increment_check.isChecked(),
            'enable_filename_suffix': self.enable_suffix_check.isChecked(),

            # ==========================================
            # Format-specific settings
            # ==========================================
            'tiff_compression': self.tiff_compression_combo.currentData(),
            'tiff_jpeg_quality': self.tiff_jpeg_quality_slider.value(),
            'gif_optimize': self.gif_optimize_check.isChecked(),
            'gif_dithering': 'floyd',
            'ico_size': self.ico_size_spinbox.value(),
            'ico_force_square': 'pad' if self.ico_force_square_pad.isChecked() else 'crop',
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

    def _get_output_mode(self) -> OutputLocationMode:
        """Get currently selected output location mode."""
        if self.output_mode_custom.isChecked():
            return OutputLocationMode.CUSTOM_FOLDER
        elif self.output_mode_source.isChecked():
            return OutputLocationMode.SAME_AS_SOURCE
        else:  # output_mode_ask
            return OutputLocationMode.ASK_EVERY_TIME

    def get_selected_format(self) -> ImageFormat:
        """Get currently selected format."""
        return self.format_combo.currentData()

    def update_original_size(self, original_bytes: int | None):
        self._original_size_bytes = original_bytes if original_bytes and original_bytes > 0 else None

    def update_estimated_size(self, size_bytes: int):
        """
        Update the estimated file size display.

        Args:
            size_bytes: Estimated file size in bytes (0 to hide)
        """
        if size_bytes > 0:
            parts = []
            parts.append(f"Est. size: {self._format_size(size_bytes)}")
            if self._original_size_bytes is not None:
                parts.append(f"Orig. size: {self._format_size(self._original_size_bytes)}")
            self.estimated_size_label.setText(" | ".join(parts))
            self.estimated_size_label.show()
        else:
            self.estimated_size_label.setText("Est. Size: —")
            self.estimated_size_label.hide()

    def _on_enable_suffix_toggled(self):
        enabled = self.enable_suffix_check.isChecked()
        self.filename_template_combo.setEnabled(enabled)
        self.custom_suffix_container.setEnabled(enabled)

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        return f"{size_bytes / 1024:.1f} KB"

    def clear_estimated_size(self):
        """
        Clear both estimated size and original size display.

        Used when switching images or disabling output preview to prevent
        stale data from previous image.
        """
        # Clear the internal original size tracker
        self._original_size_bytes = None

        # Reset label to placeholder
        self.estimated_size_label.setText("Est. Size: —")