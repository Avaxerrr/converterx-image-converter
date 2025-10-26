from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QCheckBox, QGroupBox, QPushButton, QFileDialog,
    QSpinBox, QRadioButton, QButtonGroup, QLineEdit, QToolButton,
    QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
from core.format_settings import ImageFormat, ConversionSettings, ResizeMode
from models.image_file import ImageFile


class CollapsibleSection(QWidget):
    """A collapsible section widget (accordion-style) with customizable spacing."""

    def __init__(self, title: str, content_spacing: int = 6, parent=None):
        super().__init__(parent)

        # Toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setProperty("class", "collapsible-header")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.clicked.connect(self._on_toggle)
        self.toggle_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Content area
        self.content_area = QWidget()
        self.content_area.setProperty("class", "collapsible-content")
        self.content_layout = QVBoxLayout(self.content_area)

        # ✅ CUSTOM SPACING per section
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(content_spacing)  # Use parameter

        self.content_area.hide()

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def _on_toggle(self):
        """Toggle content visibility."""
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.content_area.setVisible(checked)

    def set_content_layout(self, layout):
        """Set the layout for the collapsible content."""
        # Clear existing
        while self.content_layout.count():
            self.content_layout.takeAt(0)

        # Add new content
        if isinstance(layout, (QVBoxLayout, QHBoxLayout)):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    self.content_layout.addWidget(item.widget())
                elif item.layout():
                    self.content_layout.addLayout(item.layout())
        else:
            self.content_layout.addLayout(layout)



class SettingsPanel(QWidget):
    """Panel for conversion settings with accordion-style collapsible sections."""

    settings_changed = Signal(ConversionSettings)
    convert_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_folder = Path(Path.home() / "Downloads" / "Converted")

        # ✅ CREATE SCROLL AREA (Option A - Full Panel Scroll)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)  # Remove border

        # Create content widget (this holds all your settings)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 12, 12, 8)
        content_layout.setSpacing(6)

        # ✅ Set minimum width to prevent overflow
        content_widget.setMinimumWidth(200)

        # Build all settings inside content_layout
        self._setup_ui_content(content_layout)

        # Set content widget into scroll area
        scroll_area.setWidget(content_widget)

        # Main layout - just the scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(scroll_area)

        # Track current image dimensions
        self.current_image_width = None
        self.current_image_height = None

    def _setup_ui_content(self, layout):
        """Build all settings UI inside the provided layout."""

        # === ADD HEADER ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Title label
        self.title_label = QLabel("Settings")
        self.title_label.setObjectName("panelHeader")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Convert button
        self.convert_btn = QPushButton("Convert Selected")
        self.convert_btn.setObjectName("convert-button")
        self.convert_btn.clicked.connect(self.convert_requested.emit)
        self.convert_btn.setEnabled(False)
        layout.addWidget(self.convert_btn)

        # === OUTPUT SETTINGS ===
        output_section = CollapsibleSection("Output Settings", content_spacing=6)
        output_section.toggle_button.setChecked(True)
        output_section._on_toggle()

        output_layout = QVBoxLayout()
        output_layout.setSpacing(6)

        # Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        for fmt in ImageFormat:
            self.format_combo.addItem(fmt.value, fmt)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo, 1)
        output_layout.addLayout(format_layout)

        # Compression mode
        self.mode_quality = QRadioButton("Quality-based")
        self.mode_quality.setChecked(True)
        self.mode_quality.toggled.connect(self._on_mode_changed)
        self.mode_target = QRadioButton("Target file size")
        self.mode_target.toggled.connect(self._on_mode_changed)
        output_layout.addWidget(self.mode_quality)
        output_layout.addWidget(self.mode_target)

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
        output_layout.addWidget(self.quality_container)

        # Target size
        self.target_container = QWidget()
        target_layout = QHBoxLayout(self.target_container)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(6)
        target_layout.addWidget(QLabel("Target:"))
        self.target_size_input = QLineEdit()
        self.target_size_input.setObjectName("target-size-input")
        self.target_size_input.setPlaceholderText("500")
        self.target_size_input.textChanged.connect(self._on_settings_changed)
        self.target_unit_combo = QComboBox()
        self.target_unit_combo.setObjectName("target-unit-combo")
        self.target_unit_combo.addItems(["KB", "MB"])
        self.target_unit_combo.currentIndexChanged.connect(self._on_settings_changed)
        target_layout.addWidget(self.target_size_input)
        target_layout.addWidget(self.target_unit_combo)
        target_layout.addStretch()
        output_layout.addWidget(self.target_container)
        self.target_container.hide()

        # PNG compress
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
        self.png_level_spin.valueChanged.connect(self._on_settings_changed)
        png_label_layout.addWidget(self.png_level_spin)
        png_label_layout.addStretch()
        png_layout.addLayout(png_label_layout)

        png_note = QLabel("0=Fast, 9=Smallest")
        png_note.setProperty("class", "info-note")
        png_layout.addWidget(png_note)
        output_layout.addWidget(self.png_container)
        self.png_container.hide()

        # Checkboxes
        self.lossless_check = QCheckBox("Lossless")
        self.lossless_check.stateChanged.connect(self._on_lossless_changed)
        output_layout.addWidget(self.lossless_check)

        self.metadata_check = QCheckBox("Keep metadata")
        self.metadata_check.setChecked(True)
        self.metadata_check.stateChanged.connect(self._on_settings_changed)
        output_layout.addWidget(self.metadata_check)

        output_section.set_content_layout(output_layout)
        layout.addWidget(output_section)

        # === RESIZE OPTIONS ===
        resize_section = CollapsibleSection("Resize Options", content_spacing=5)
        resize_layout = QVBoxLayout()
        resize_layout.setSpacing(4)

        # Current image info label (shown when image is selected)
        self.current_dims_label = QLabel("No image selected")
        self.current_dims_label.setObjectName("dims-info-label")
        self.current_dims_label.setAlignment(Qt.AlignCenter)
        resize_layout.addWidget(self.current_dims_label)

        self.resize_none = QRadioButton("No resize")
        self.resize_none.setChecked(True)
        self.resize_none.toggled.connect(self._on_resize_mode_changed)

        self.resize_percentage = QRadioButton("Scale by %")
        self.resize_percentage.toggled.connect(self._on_resize_mode_changed)

        self.resize_max_dims = QRadioButton("Max dimensions")
        self.resize_max_dims.toggled.connect(self._on_resize_mode_changed)

        resize_layout.addWidget(self.resize_none)
        resize_layout.addWidget(self.resize_percentage)
        resize_layout.addWidget(self.resize_max_dims)

        # Percentage slider
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

        resize_layout.addWidget(self.percentage_container)
        self.percentage_container.hide()

        # Max dimensions
        self.dimensions_container = QWidget()
        dimensions_layout = QVBoxLayout(self.dimensions_container)
        dimensions_layout.setContentsMargins(16, 0, 0, 0)
        dimensions_layout.setSpacing(4)

        dim_input_layout = QHBoxLayout()
        dim_input_layout.addWidget(QLabel("Width:"))
        self.max_width_input = QSpinBox()
        self.max_width_input.setMinimum(1)
        self.max_width_input.setMaximum(10000)
        self.max_width_input.setValue(1920)
        self.max_width_input.setSuffix(" px")
        self.max_width_input.valueChanged.connect(self._on_settings_changed)
        dim_input_layout.addWidget(self.max_width_input)
        dim_input_layout.addStretch()
        dimensions_layout.addLayout(dim_input_layout)

        dim_height_layout = QHBoxLayout()
        dim_height_layout.addWidget(QLabel("Height:"))
        self.max_height_input = QSpinBox()
        self.max_height_input.setMinimum(1)
        self.max_height_input.setMaximum(10000)
        self.max_height_input.setValue(1080)
        self.max_height_input.setSuffix(" px")
        self.max_height_input.valueChanged.connect(self._on_settings_changed)
        dim_height_layout.addWidget(self.max_height_input)
        dim_height_layout.addStretch()
        dimensions_layout.addLayout(dim_height_layout)

        self.aspect_ratio_check = QCheckBox("Keep aspect ratio")
        self.aspect_ratio_check.setChecked(True)
        self.aspect_ratio_check.stateChanged.connect(self._on_settings_changed)
        dimensions_layout.addWidget(self.aspect_ratio_check)

        # Preview label for max dimensions mode
        self.dimensions_preview_label = QLabel("Output: 1920 × 1080 px")
        self.dimensions_preview_label.setObjectName("resize-preview-label")
        self.dimensions_preview_label.setAlignment(Qt.AlignCenter)
        dimensions_layout.addWidget(self.dimensions_preview_label)

        resize_layout.addWidget(self.dimensions_container)
        self.dimensions_container.hide()

        resize_section.set_content_layout(resize_layout)
        layout.addWidget(resize_section)

        # === ADVANCED OPTIONS ===
        # === ADVANCED OPTIONS ===
        self.advanced_section = CollapsibleSection("Advanced Options",
                                                   content_spacing=4)  # ✅ Store as instance variable
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(4)

        # WebP method
        webp_method_layout = QHBoxLayout()
        webp_method_layout.addWidget(QLabel("Method:"))
        self.webp_method_spin = QSpinBox()
        self.webp_method_spin.setMinimum(0)
        self.webp_method_spin.setMaximum(6)
        self.webp_method_spin.setValue(6)
        self.webp_method_spin.setToolTip("0=Fast, 6=Best quality")
        self.webp_method_spin.valueChanged.connect(self._on_settings_changed)
        webp_method_layout.addWidget(self.webp_method_spin)
        webp_method_layout.addStretch()
        self.webp_method_widget = QWidget()
        self.webp_method_widget.setLayout(webp_method_layout)
        advanced_layout.addWidget(self.webp_method_widget)

        # ✅ NEW: WebP subsampling
        webp_subsampling_layout = QHBoxLayout()
        webp_subsampling_layout.addWidget(QLabel("Subsampling:"))
        self.webp_subsampling_combo = QComboBox()
        self.webp_subsampling_combo.addItems(["4:4:4", "4:2:2", "4:2:0"])
        self.webp_subsampling_combo.setCurrentIndex(2)  # Default to 4:2:0
        self.webp_subsampling_combo.setToolTip("Chroma subsampling (4:4:4=Best, 4:2:0=Smallest)")
        self.webp_subsampling_combo.currentIndexChanged.connect(self._on_settings_changed)
        webp_subsampling_layout.addWidget(self.webp_subsampling_combo)
        webp_subsampling_layout.addStretch()
        self.webp_subsampling_widget = QWidget()
        self.webp_subsampling_widget.setLayout(webp_subsampling_layout)
        advanced_layout.addWidget(self.webp_subsampling_widget)

        # AVIF speed
        avif_speed_layout = QHBoxLayout()
        avif_speed_layout.addWidget(QLabel("Speed:"))
        self.avif_speed_spin = QSpinBox()
        self.avif_speed_spin.setMinimum(0)
        self.avif_speed_spin.setMaximum(10)
        self.avif_speed_spin.setValue(4)
        self.avif_speed_spin.setToolTip("0=Slowest/Best, 10=Fastest")
        self.avif_speed_spin.valueChanged.connect(self._on_settings_changed)
        avif_speed_layout.addWidget(self.avif_speed_spin)
        avif_speed_layout.addStretch()
        self.avif_speed_widget = QWidget()
        self.avif_speed_widget.setLayout(avif_speed_layout)
        advanced_layout.addWidget(self.avif_speed_widget)

        # ✅ NEW: AVIF range
        avif_range_layout = QHBoxLayout()
        avif_range_layout.addWidget(QLabel("Range:"))
        self.avif_range_combo = QComboBox()
        self.avif_range_combo.addItems(["Limited", "Full"])
        self.avif_range_combo.setCurrentIndex(1)  # Default to Full
        self.avif_range_combo.setToolTip("Color range (Full=Better quality)")
        self.avif_range_combo.currentIndexChanged.connect(self._on_settings_changed)
        avif_range_layout.addWidget(self.avif_range_combo)
        avif_range_layout.addStretch()
        self.avif_range_widget = QWidget()
        self.avif_range_widget.setLayout(avif_range_layout)
        advanced_layout.addWidget(self.avif_range_widget)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("reset-button")
        reset_btn.clicked.connect(self._reset_advanced_settings)
        advanced_layout.addWidget(reset_btn)

        self.advanced_section.set_content_layout(advanced_layout)
        layout.addWidget(self.advanced_section)


        # Output folder
        folder_group = QGroupBox("Output Folder")
        folder_layout = QVBoxLayout(folder_group)
        folder_layout.setSpacing(6)

        folder_select_layout = QHBoxLayout()
        self.folder_label = QLabel(str(self.output_folder))
        self.folder_label.setObjectName("folder-label")
        self.folder_label.setTextFormat(Qt.PlainText)
        self.folder_label.setWordWrap(False)
        self.folder_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setObjectName("browse-button")
        self.browse_btn.clicked.connect(self._browse_output_folder)

        folder_select_layout.addWidget(self.folder_label, 1)
        folder_select_layout.addWidget(self.browse_btn)
        folder_layout.addLayout(folder_select_layout)
        layout.addWidget(folder_group)

        layout.addStretch()
        self._on_format_changed()

    def _reset_advanced_settings(self):
        """Reset advanced settings to defaults."""
        # WebP defaults
        self.webp_method_spin.setValue(6)
        self.webp_subsampling_combo.setCurrentIndex(2)  # 4:2:0

        # AVIF defaults
        self.avif_speed_spin.setValue(4)
        self.avif_range_combo.setCurrentIndex(1)  # Full

        self._on_settings_changed()

    def _on_mode_changed(self):
        """Handle compression mode change."""
        if self.mode_quality.isChecked():
            self.quality_container.show()
            self.target_container.hide()
        else:
            self.quality_container.hide()
            self.target_container.show()
        self._on_settings_changed()

    def _on_resize_mode_changed(self):
        """Handle resize mode change."""
        if self.resize_none.isChecked():
            self.percentage_container.hide()
            self.dimensions_container.hide()
        elif self.resize_percentage.isChecked():
            self.percentage_container.show()
            self.dimensions_container.hide()
        elif self.resize_max_dims.isChecked():
            self.percentage_container.hide()
            self.dimensions_container.show()

        self._update_resize_preview()
        self._on_settings_changed()

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
            self.advanced_section.hide()  # ✅ Hide advanced for PNG
        else:
            self.mode_quality.show()
            self.mode_target.show()
            self.png_container.hide()
            self._on_mode_changed()

            if format_enum == ImageFormat.JPEG:
                self.lossless_check.hide()
                self.advanced_section.hide()  # ✅ Hide advanced for JPEG
                self.webp_method_widget.hide()
                self.webp_subsampling_widget.hide()
                self.avif_speed_widget.hide()
                self.avif_range_widget.hide()
            elif format_enum == ImageFormat.WEBP:
                self.lossless_check.show()
                self.advanced_section.show()  # ✅ Show advanced for WebP
                self.webp_method_widget.show()
                self.webp_subsampling_widget.show()
                self.avif_speed_widget.hide()
                self.avif_range_widget.hide()
            elif format_enum == ImageFormat.AVIF:
                self.lossless_check.show()
                self.advanced_section.show()  # ✅ Show advanced for AVIF
                self.webp_method_widget.hide()
                self.webp_subsampling_widget.hide()
                self.avif_speed_widget.show()
                self.avif_range_widget.show()

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

    def _on_percentage_changed(self, value: int):
        """Handle percentage slider change."""
        self.percentage_value_label.setText(f"{value}%")
        self._update_resize_preview()
        self._on_settings_changed()

    def _on_dimensions_changed(self):
        """Handle max dimensions input change."""
        self._update_resize_preview()  # Update preview
        self._on_settings_changed()

    def _on_settings_changed(self):
        """Emit settings changed signal."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)

    def _browse_output_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", str(self.output_folder)
        )
        if folder:
            self.output_folder = Path(folder)
            self.folder_label.setText(str(self.output_folder))

    def get_settings(self) -> ConversionSettings:
        """Get current conversion settings."""
        format_enum = self.format_combo.currentData()

        if self.resize_none.isChecked():
            resize_mode = ResizeMode.NONE
        elif self.resize_percentage.isChecked():
            resize_mode = ResizeMode.PERCENTAGE
        else:
            resize_mode = ResizeMode.MAX_DIMENSIONS

        settings = ConversionSettings(
            output_format=format_enum,
            quality=self.quality_slider.value(),
            lossless=self.lossless_check.isChecked() if self.lossless_check.isVisible() else False,
            keep_metadata=self.metadata_check.isChecked(),
            resize_mode=resize_mode,
            resize_percentage=self.percentage_slider.value(),
            max_width=self.max_width_input.value() if resize_mode == ResizeMode.MAX_DIMENSIONS else None,
            max_height=self.max_height_input.value() if resize_mode == ResizeMode.MAX_DIMENSIONS else None,
            maintain_aspect_ratio=self.aspect_ratio_check.isChecked()
        )

        if format_enum == ImageFormat.PNG:
            settings.png_compress_level = self.png_level_spin.value()

        if self.mode_target.isChecked() and self.target_size_input.text():
            try:
                size_value = float(self.target_size_input.text())
                if self.target_unit_combo.currentText() == "MB":
                    size_value *= 1024
                settings.target_size_kb = size_value
            except ValueError:
                pass

        if format_enum == ImageFormat.WEBP:
            settings.webp_method = self.webp_method_spin.value()
            # ✅ Add subsampling (convert to tuple format Pillow expects)
            subsampling_map = {"4:4:4": (1, 1), "4:2:2": (2, 1), "4:2:0": (2, 2)}
            settings.webp_subsampling = subsampling_map[self.webp_subsampling_combo.currentText()]

        elif format_enum == ImageFormat.AVIF:
            settings.avif_speed = self.avif_speed_spin.value()
            # ✅ Add range
            settings.avif_range = self.avif_range_combo.currentText().lower()

        return settings

    def get_output_folder(self) -> Path:
        """Get selected output folder."""
        return self.output_folder

    def set_convert_enabled(self, enabled: bool):
        """Enable/disable convert button."""
        self.convert_btn.setEnabled(enabled)

    def set_current_image(self, image_file: ImageFile):
        """
        Update the settings panel with the currently selected image.
        This allows resize preview calculations.
        """
        if image_file:
            self.current_image_width = image_file.width
            self.current_image_height = image_file.height

            # Update the info label
            self.current_dims_label.setText(
                f"Original: {image_file.width} × {image_file.height} px"
            )
            self.current_dims_label.setStyleSheet("color: #cccccc;")
        else:
            self.current_image_width = None
            self.current_image_height = None
            self.current_dims_label.setText("No image selected")
            self.current_dims_label.setStyleSheet("color: #858585;")

        # Update all previews
        self._update_resize_preview()

    def _update_resize_preview(self):
        """Calculate and display the output dimensions preview."""
        if not self.current_image_width or not self.current_image_height:
            # No image selected
            self.percentage_preview_label.setText("Select an image to preview")
            self.percentage_preview_label.setStyleSheet("color: #858585;")
            self.dimensions_preview_label.setText("Select an image to preview")
            self.dimensions_preview_label.setStyleSheet("color: #858585;")
            return

        # Calculate based on resize mode
        if self.resize_none.isChecked():
            # No resize - output = input
            preview_text = f"Output: {self.current_image_width} × {self.current_image_height} px"

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

        elif self.resize_max_dims.isChecked():
            # Max dimensions with aspect ratio
            max_w = self.max_width_input.value()
            max_h = self.max_height_input.value()

            if self.aspect_ratio_check.isChecked():
                # Calculate maintaining aspect ratio
                w_ratio = max_w / self.current_image_width
                h_ratio = max_h / self.current_image_height
                scale = min(w_ratio, h_ratio, 1.0)  # Don't upscale

                output_width = int(self.current_image_width * scale)
                output_height = int(self.current_image_height * scale)
            else:
                # Exact dimensions (may distort)
                output_width = min(max_w, self.current_image_width)
                output_height = min(max_h, self.current_image_height)

            preview_text = f"→ Output: {output_width} × {output_height} px"
            self.dimensions_preview_label.setText(preview_text)

            # Check if upscaling
            if output_width > self.current_image_width or output_height > self.current_image_height:
                self.dimensions_preview_label.setStyleSheet("color: #f48771;")  # Warning
            else:
                self.dimensions_preview_label.setStyleSheet("color: #4ec9b0;")  # Success
