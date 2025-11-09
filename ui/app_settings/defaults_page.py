"""
Default Settings Page

Settings page for default conversion settings:
- Default Quality
- Default Output Format
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QComboBox, QGroupBox, QCheckBox, QLineEdit, QPushButton, QRadioButton, QFileDialog
)
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController

from core.format_settings import ImageFormat, FilenameTemplate, OutputLocationMode


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
        # Output defaults
        # ============================================================
        output_group = QGroupBox("Output defaults")
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(14)

        # ---- Output location ----
        loc_group = QGroupBox("Output location")
        loc_layout = QVBoxLayout(loc_group)
        loc_layout.setSpacing(8)

        loc_help = QLabel("Choose where converted files are saved by default for new sessions.")

        loc_help.setWordWrap(True)
        loc_layout.addWidget(loc_help)

        self.default_mode_same = QRadioButton("Same as Source")
        self.default_mode_ask = QRadioButton("Ask Every Time")
        self.default_mode_custom = QRadioButton("Custom Folder")
        loc_layout.addWidget(self.default_mode_same)
        loc_layout.addWidget(self.default_mode_ask)
        loc_layout.addWidget(self.default_mode_custom)

        # Tie folder row enablement to radio selection
        self.default_mode_custom.toggled.connect(self._on_location_mode_changed)
        self.default_mode_same.toggled.connect(self._on_location_mode_changed)
        self.default_mode_ask.toggled.connect(self._on_location_mode_changed)

        # Indented default custom folder (enabled only for Custom)
        folder_row = QHBoxLayout()
        folder_row.setContentsMargins(20, 0, 0, 0)
        self.default_custom_folder_edit = QLineEdit()
        self.default_custom_folder_edit.setReadOnly(True)
        self.default_custom_folder_browse = QPushButton("Browse")
        self.default_custom_folder_browse.clicked.connect(self._browse_default_folder)
        folder_row.addWidget(self.default_custom_folder_edit, 1)
        folder_row.addWidget(self.default_custom_folder_browse)
        loc_layout.addLayout(folder_row)

        output_layout.addWidget(loc_group)

        # ---- Filename suffix ----
        suffix_group = QGroupBox("Filename suffix")
        suffix_layout = QVBoxLayout(suffix_group)
        suffix_layout.setSpacing(8)

        suffix_help = QLabel(
            "Append a suffix to output filenames to avoid overwriting originals and make results easier to identify."
        )

        suffix_help.setWordWrap(True)
        suffix_layout.addWidget(suffix_help)

        self.default_enable_suffix = QCheckBox("Enable filename suffix")
        self.default_enable_suffix.setChecked(True)
        self.default_enable_suffix.toggled.connect(self._on_default_suffix_toggled)
        suffix_layout.addWidget(self.default_enable_suffix)

        template_row = QHBoxLayout()
        template_row.setContentsMargins(20, 0, 0, 0)
        template_row.addWidget(QLabel("Suffix:"))
        self.default_template_combo = QComboBox()
        self.default_template_combo.addItem("_converted", FilenameTemplate.CONVERTED)
        self.default_template_combo.addItem("_[format]", FilenameTemplate.FORMAT)
        self.default_template_combo.addItem("_Q[quality]", FilenameTemplate.QUALITY)
        self.default_template_combo.addItem("Custom...", FilenameTemplate.CUSTOM)
        self.default_template_combo.currentIndexChanged.connect(self._on_default_template_changed)
        template_row.addWidget(self.default_template_combo, 1)
        suffix_layout.addLayout(template_row)

        self.default_custom_suffix_container = QWidget()
        custom_row = QHBoxLayout(self.default_custom_suffix_container)
        custom_row.setContentsMargins(20, 0, 0, 0)
        custom_row.addWidget(QLabel("Custom:"))
        self.default_custom_suffix_input = QLineEdit()
        self.default_custom_suffix_input.setPlaceholderText("e.g., _optimized")
        custom_row.addWidget(self.default_custom_suffix_input, 1)
        self.default_custom_suffix_container.hide()
        suffix_layout.addWidget(self.default_custom_suffix_container)

        output_layout.addWidget(suffix_group)

        # ---- Collision handling ----
        collision_group = QGroupBox("Collision handling")
        collision_layout = QVBoxLayout(collision_group)
        collision_layout.setSpacing(8)

        collision_help = QLabel(
            "When a file with the same name exists, automatically append a number (…_1, …_2) to avoid overwriting."
        )

        collision_help.setWordWrap(True)
        collision_layout.addWidget(collision_help)

        self.default_auto_increment = QCheckBox("Auto-increment if file exists")
        self.default_auto_increment.setChecked(True)
        collision_layout.addWidget(self.default_auto_increment)

        output_layout.addWidget(collision_group)

        self.layout().addWidget(output_group)

        # ============================================================
        # Spacer
        # ============================================================
        layout.addStretch()

        # Initial state before values are loaded
        self._on_location_mode_changed()
        self._on_default_suffix_toggled()
        self._on_default_template_changed()

    def _browse_default_folder(self):
        start = self.default_custom_folder_edit.text().strip() or str(Path.home() / "Pictures" / "Converter")
        folder = QFileDialog.getExistingDirectory(self, "Select Default Output Folder", start)
        if folder:
            self.default_custom_folder_edit.setText(folder)

    def _on_default_template_changed(self):
        tmpl = self.default_template_combo.currentData()
        if tmpl == FilenameTemplate.CUSTOM:
            self.default_custom_suffix_container.show()
        else:
            self.default_custom_suffix_container.hide()

    def load_from_controller(self) -> None:
        """Load current settings from controller into UI."""
        # Quality
        self.quality_slider.setValue(self.controller.get_default_quality())

        # Format
        format_enum = self.controller.get_default_output_format()
        format_map = {
            ImageFormat.WEBP: 0,
            ImageFormat.AVIF: 1,
            ImageFormat.JPEG: 2,
            ImageFormat.PNG: 3
        }
        self.format_combo.setCurrentIndex(format_map.get(format_enum, 0))

        # Location mode
        mode = self.controller.get_default_output_location_mode()
        self.default_mode_custom.setChecked(mode == OutputLocationMode.CUSTOM_FOLDER)
        self.default_mode_same.setChecked(mode == OutputLocationMode.SAME_AS_SOURCE)
        self.default_mode_ask.setChecked(mode == OutputLocationMode.ASK_EVERY_TIME)

        # Default custom folder
        folder = self.controller.get_default_custom_output_folder()
        self.default_custom_folder_edit.setText(str(folder))

        # Suffix enable
        self.default_enable_suffix.setChecked(self.controller.get_default_enable_filename_suffix())

        # Template + custom text
        tmpl = self.controller.get_default_filename_template()
        index_map = {
            FilenameTemplate.CONVERTED: 0,
            FilenameTemplate.FORMAT: 1,
            FilenameTemplate.QUALITY: 2,
            FilenameTemplate.CUSTOM: 3,
        }
        self.default_template_combo.setCurrentIndex(index_map.get(tmpl, 0))
        self.default_custom_suffix_input.setText(self.controller.get_default_custom_suffix())

        # Auto-increment
        self.default_auto_increment.setChecked(self.controller.get_default_auto_increment())

        # Enforce visibility/enablement after restoring values (order matters)
        self._on_default_template_changed()
        self._on_location_mode_changed()
        self._on_default_suffix_toggled()

    def _on_default_suffix_toggled(self) -> None:
        enabled = self.default_enable_suffix.isChecked()
        self.default_template_combo.setEnabled(enabled)
        self.default_custom_suffix_container.setEnabled(enabled)
        self.default_custom_suffix_input.setEnabled(enabled)

    def save_to_controller(self) -> None:
        """Save UI values back to controller."""
        # Quality
        self.controller.set_default_quality(self.quality_slider.value())

        # Format
        index_to_format = {
            0: ImageFormat.WEBP,
            1: ImageFormat.AVIF,
            2: ImageFormat.JPEG,
            3: ImageFormat.PNG
        }
        format_enum = index_to_format[self.format_combo.currentIndex()]
        self.controller.set_default_output_format(format_enum)

        # Location mode
        if self.default_mode_custom.isChecked():
            self.controller.set_default_output_location_mode(OutputLocationMode.CUSTOM_FOLDER)
        elif self.default_mode_same.isChecked():
            self.controller.set_default_output_location_mode(OutputLocationMode.SAME_AS_SOURCE)
        else:
            self.controller.set_default_output_location_mode(OutputLocationMode.ASK_EVERY_TIME)

        # Default custom folder
        folder_text = self.default_custom_folder_edit.text().strip()
        if not folder_text:
            folder_text = str(Path.home() / "Pictures" / "Converter")
        self.controller.set_default_custom_output_folder(Path(folder_text))

        # Suffix enable
        self.controller.set_default_enable_filename_suffix(self.default_enable_suffix.isChecked())

        # Template + custom text
        tmpl = self.default_template_combo.currentData()
        self.controller.set_default_filename_template(tmpl)
        self.controller.set_default_custom_suffix(self.default_custom_suffix_input.text().strip())

        # Auto-increment
        self.controller.set_default_auto_increment(self.default_auto_increment.isChecked())

    def _on_location_mode_changed(self) -> None:
        is_custom = self.default_mode_custom.isChecked()
        self.default_custom_folder_edit.setEnabled(is_custom)
        self.default_custom_folder_browse.setEnabled(is_custom)