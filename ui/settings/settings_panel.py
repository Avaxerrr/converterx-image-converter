"""
Main settings panel coordinator.

Composes output, resize, and advanced settings widgets into collapsible sections.
Aggregates settings from all child components and provides a unified interface.
"""
from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QPushButton, QHBoxLayout, QGroupBox, \
    QFileDialog
from PySide6.QtCore import Signal
from pathlib import Path

from core.format_settings import ConversionSettings, ImageFormat
from models.image_file import ImageFile

from .collapsible_section import CollapsibleSection
from .output_settings import OutputSettingsWidget
from .resize_settings import ResizeSettingsWidget
from .advanced_settings import AdvancedSettingsWidget


class SettingsPanel(QWidget):
    """Main settings panel that coordinates all settings components."""

    settings_changed = Signal(ConversionSettings)
    convert_requested = Signal()
    app_settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image = None
        self._setup_ui()
        self._connect_signals()
        # Emit initial settings
        self._on_settings_changed()

    def _setup_ui(self):
        """Build the settings panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        # Container widget inside scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 12, 12, 8)
        container_layout.setSpacing(6)
        container.setMinimumWidth(200)

        # Header with title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title_label = QLabel("Settings")
        title_label.setObjectName("panelHeader")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        container_layout.addLayout(header_layout)

        # Convert Button + App Settings Button
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)

        # Convert button
        self.convert_btn = QPushButton("Convert Selected")
        self.convert_btn.setObjectName("convert-button")
        self.convert_btn.setIcon(QIcon("icons/convert-image.svg"))
        self.convert_btn.clicked.connect(self.convert_requested.emit)
        self.convert_btn.setEnabled(False)

        # App Settings button (icon only)
        self.app_settings_btn = QPushButton()
        self.app_settings_btn.setObjectName("app-settings-button")
        self.app_settings_btn.setIcon(QIcon("icons/settings.svg"))
        self.app_settings_btn.setToolTip("App Settings")
        self.app_settings_btn.clicked.connect(self.app_settings_requested.emit)

        button_layout.addWidget(self.convert_btn, 1)
        button_layout.addWidget(self.app_settings_btn)

        container_layout.addLayout(button_layout)

        # Output Settings Section (now includes output location + filename)
        self.output_widget = OutputSettingsWidget()
        output_section = CollapsibleSection("Output Settings", content_spacing=6)
        output_section.set_content_layout(self.output_widget.layout())
        output_section.toggle_button.setChecked(True)
        output_section._on_toggle()
        container_layout.addWidget(output_section)

        # Resize Settings Section
        self.resize_widget = ResizeSettingsWidget()
        resize_section = CollapsibleSection("Resize Options", content_spacing=4)
        resize_section.set_content_layout(self.resize_widget.layout())
        container_layout.addWidget(resize_section)

        # Advanced Settings Section
        self.advanced_widget = AdvancedSettingsWidget()
        self.advanced_section = CollapsibleSection("Advanced Options", content_spacing=4)
        self.advanced_section.set_content_layout(self.advanced_widget.layout())
        container_layout.addWidget(self.advanced_section)

        container_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.update_advanced_visibility()

    def _connect_signals(self):
        """Connect signals from child widgets."""
        # Output settings
        self.output_widget.settings_changed.connect(self._on_settings_changed)
        self.output_widget.format_changed.connect(self._on_format_changed)

        # Resize settings
        self.resize_widget.settings_changed.connect(self._on_settings_changed)

        # Advanced settings
        self.advanced_widget.settings_changed.connect(self._on_settings_changed)

    def _on_format_changed(self, format_enum: ImageFormat):
        """Handle format change - update advanced settings visibility."""
        self.advanced_widget.set_active_format(format_enum)
        self.update_advanced_visibility()  # FIXED: Remove underscore
        self._on_settings_changed()

    def update_advanced_visibility(self):  # FIXED: Renamed from _update_advanced_visibility
        """Show/hide advanced section based on format."""
        current_format = self.output_widget.get_selected_format()
        should_show = self.advanced_widget.should_show_for_format(current_format)

        if should_show:
            self.advanced_section.show()
        else:
            self.advanced_section.hide()

    def _on_settings_changed(self):
        """Aggregate settings from all widgets and emit."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)

    def get_settings(self) -> ConversionSettings:
        """Aggregate and return settings from all components."""
        output_settings = self.output_widget.get_settings()
        resize_settings = self.resize_widget.get_settings()
        advanced_settings = self.advanced_widget.get_settings()

        settings = ConversionSettings(
            output_format=output_settings["output_format"],
            quality=output_settings["quality"],
            lossless=output_settings["lossless"],
            keep_metadata=output_settings["keep_metadata"],
            png_compress_level=output_settings["png_compress_level"],
            target_size_kb=output_settings["target_size_kb"],

            # Resize settings
            resize_mode=resize_settings["resize_mode"],
            resize_percentage=resize_settings["resize_percentage"],
            target_width_px=resize_settings["target_width_px"],
            target_height_px=resize_settings["target_height_px"],
            max_width_px=resize_settings["max_width_px"],
            max_height_px=resize_settings["max_height_px"],
            allow_upscaling=resize_settings["allow_upscaling"],

            # Advanced settings (format-specific)
            webp_method=advanced_settings.get("webp_method", 6),
            webp_subsampling=advanced_settings.get("webp_subsampling", (2, 2)),
            avif_speed=advanced_settings.get("avif_speed", 4),
            avif_range=advanced_settings.get("avif_range", "full"),

            # Output location and filename settings
            output_location_mode=output_settings["output_location_mode"],
            custom_output_folder=output_settings["custom_output_folder"],
            filename_template=output_settings["filename_template"],
            enable_filename_suffix=output_settings["enable_filename_suffix"],
            custom_suffix=output_settings["custom_suffix"],
            auto_increment=output_settings["auto_increment"],
        )

        return settings

    def set_current_image(self, image_file: ImageFile):
        """Update with current image (compatibility method)."""
        self.update_preview(image_file)

    def update_preview(self, image_file: ImageFile):
        """Update with current image for preview calculations."""
        self.current_image = image_file

        if image_file:
            self.resize_widget.set_current_image(
                image_file.width,
                image_file.height
            )
        else:
            self.resize_widget.clear_current_image()

    def set_convert_enabled(self, enabled: bool):
        """Enable/disable convert button."""
        self.convert_btn.setEnabled(enabled)