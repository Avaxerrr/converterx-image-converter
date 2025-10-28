"""
Main settings panel coordinator.

Composes output, resize, and advanced settings widgets into collapsible sections.
Aggregates settings from all child components and provides a unified interface.
"""
from PySide6.QtGui import Qt
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
    convert_requested = Signal()  # ← ADDED: Missing signal

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

        # ← ADDED: Header with title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        title_label = QLabel("Settings")
        title_label.setObjectName("panelHeader")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        container_layout.addLayout(header_layout)

        # ← ADDED: Convert button
        self.convert_btn = QPushButton("Convert Selected")
        self.convert_btn.setObjectName("convert-button")
        self.convert_btn.clicked.connect(self.convert_requested.emit)
        self.convert_btn.setEnabled(False)
        container_layout.addWidget(self.convert_btn)

        # === Output Settings Section ===
        self.output_widget = OutputSettingsWidget()
        output_section = CollapsibleSection("Output Settings", content_spacing=6)
        output_section.set_content_layout(self.output_widget.layout())
        output_section.toggle_button.setChecked(True)  # ← Start expanded
        output_section._on_toggle()  # ← Apply expansion
        container_layout.addWidget(output_section)

        # === Resize Settings Section ===
        self.resize_widget = ResizeSettingsWidget()
        resize_section = CollapsibleSection("Resize Options", content_spacing=4)
        resize_section.set_content_layout(self.resize_widget.layout())
        container_layout.addWidget(resize_section)

        # === Advanced Settings Section ===
        self.advanced_widget = AdvancedSettingsWidget()
        self.advanced_section = CollapsibleSection("Advanced Options", content_spacing=4)
        self.advanced_section.set_content_layout(self.advanced_widget.layout())
        container_layout.addWidget(self.advanced_section)

        # === Output Folder (OUTSIDE collapsible sections) ===
        folder_group = QGroupBox("Output Folder")
        folder_layout = QVBoxLayout(folder_group)
        folder_layout.setSpacing(6)

        folder_select_layout = QHBoxLayout()
        self.folder_label = QLabel(str(self.output_widget.output_folder))
        self.folder_label.setObjectName("folder-label")
        self.folder_label.setTextFormat(Qt.PlainText)
        self.folder_label.setWordWrap(False)
        self.folder_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("browse-button")
        browse_btn.clicked.connect(self._browse_output_folder)

        folder_select_layout.addWidget(self.folder_label, 1)
        folder_select_layout.addWidget(browse_btn)
        folder_layout.addLayout(folder_select_layout)
        container_layout.addWidget(folder_group)

        container_layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Update advanced section visibility based on initial format
        self._update_advanced_visibility()

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
        self._update_advanced_visibility()
        self._on_settings_changed()

    def _update_advanced_visibility(self):
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

        # Merge all settings into ConversionSettings object
        settings = ConversionSettings(
            output_format=output_settings['output_format'],
            quality=output_settings['quality'],
            lossless=output_settings['lossless'],
            keep_metadata=output_settings['keep_metadata'],
            png_compress_level=output_settings['png_compress_level'],
            target_size_kb=output_settings['target_size_kb'],
            resize_mode=resize_settings['resize_mode'],
            resize_percentage=resize_settings['resize_percentage'],
            max_width=resize_settings['max_width'],
            max_height=resize_settings['max_height'],
            maintain_aspect_ratio=resize_settings['maintain_aspect_ratio'],
            # Advanced settings (format-specific)
            webp_method=advanced_settings.get('webp_method', 6),
            webp_subsampling=advanced_settings.get('webp_subsampling', (2, 2)),
            avif_speed=advanced_settings.get('avif_speed', 4),
            avif_range=advanced_settings.get('avif_range', 'full')
        )

        return settings

    # ← ADDED: Method for compatibility (calls update_preview internally)
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

    def set_output_directory(self, path: Path):
        """Set output directory path."""
        self.output_widget.output_folder = path
        self.folder_label.setText(str(path))

    def get_output_directory(self) -> Path:
        """Get output directory path."""
        return self.output_widget.output_folder

    # ← ADDED: Alias for compatibility
    def get_output_folder(self) -> Path:
        """Get output folder path (alias for get_output_directory)."""
        return self.get_output_directory()

    # ← ADDED: Missing method
    def set_convert_enabled(self, enabled: bool):
        """Enable/disable convert button."""
        self.convert_btn.setEnabled(enabled)

    def _browse_output_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", str(self.output_widget.output_folder)
        )
        if folder:
            self.output_widget.output_folder = Path(folder)
            self.folder_label.setText(str(folder))
