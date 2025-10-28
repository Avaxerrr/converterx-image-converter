from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QListWidgetItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon
from typing import List
from pathlib import Path
from models.image_file import ImageFile


class FileListWidget(QWidget):
    """Widget displaying the list of images to convert."""

    # Signals
    file_selected = Signal(ImageFile)
    files_dropped = Signal(list)  # Emits List[Path]

    # Icon paths mapping
    ICON_PATHS = {
        'JPEG': 'icons/jpg_icons.png',
        'JPG': 'icons/jpg_icons.png',
        'PNG': 'icons/png_icons.png',
        'WEBP': 'icons/webp_icons.png',
        'AVIF': 'icons/avif_icon.png',
        'BMP': 'icons/bmp_icon.png',
        'TIFF': 'icons/tiff_icon.png',
        'TIF': 'icons/tiff_icon.png',
        'GIF': 'icons/gif_icon.png',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_files: List[ImageFile] = []
        self._setup_ui()

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _get_format_icon(self, format_name: str) -> QIcon:
        """Get icon for a specific file format from file path."""
        if not format_name:
            return QIcon()

        format_upper = format_name.upper()
        icon_path = self.ICON_PATHS.get(format_upper, '')

        if icon_path and Path(icon_path).exists():
            return QIcon(icon_path)

        return QIcon()

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 8, 8)
        layout.setSpacing(8)

        # Header with title and status count
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Title label
        self.title_label = QLabel("Files")
        self.title_label.setObjectName("titleLabel")
        header_layout.addWidget(self.title_label)

        # Status label (file count)
        self.status_label = QLabel("0")
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Drag & drop hint label (shown when empty) - TAKES UP SPACE
        self.drag_hint_label = QLabel("Drag & drop images here\nor click 'Add files'")
        self.drag_hint_label.setObjectName("dragHintLabel")
        self.drag_hint_label.setAlignment(Qt.AlignCenter)
        self.drag_hint_label.setWordWrap(True)
        # CRITICAL: Make it expand to fill available space like the list does
        self.drag_hint_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.drag_hint_label)

        # File list with optimized settings
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("fileListWidget")
        self.list_widget.setIconSize(QSize(20, 20))
        self.list_widget.setSpacing(4)
        self.list_widget.setWordWrap(False)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Connect signals for both click and keyboard navigation
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(self.list_widget)

        # Initially show hint, hide list
        self.list_widget.hide()

        # Buttons - horizontal layout at bottom
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.add_btn = QPushButton("Add files")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setMinimumHeight(32)
        self.add_btn.setIcon(QIcon('icons/add_files.png'))

        self.clear_btn = QPushButton("Clear files")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setMinimumHeight(32)
        self.clear_btn.setIcon(QIcon('icons/delete_files.png'))

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

    def _on_item_clicked(self):
        """Handle list item click."""
        selected = self.get_selected_file()
        if selected:
            self.file_selected.emit(selected)

    def _on_current_item_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle selection change via keyboard navigation."""
        if current:
            selected = self.get_selected_file()
            if selected:
                self.file_selected.emit(selected)

    def dragEnterEvent(self, event):
        """Accept drag events with files."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Set property for QSS styling
            self.drag_hint_label.setProperty("dragging", True)
            self.drag_hint_label.style().unpolish(self.drag_hint_label)
            self.drag_hint_label.style().polish(self.drag_hint_label)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave."""
        self.drag_hint_label.setProperty("dragging", False)
        self.drag_hint_label.style().unpolish(self.drag_hint_label)
        self.drag_hint_label.style().polish(self.drag_hint_label)

    def dragMoveEvent(self, event):
        """Accept drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle dropped files."""
        # Remove dragging property
        self.drag_hint_label.setProperty("dragging", False)
        self.drag_hint_label.style().unpolish(self.drag_hint_label)
        self.drag_hint_label.style().polish(self.drag_hint_label)

        if not event.mimeData().hasUrls():
            event.ignore()
            return

        urls = event.mimeData().urls()
        file_paths = []

        for url in urls:
            path = Path(url.toLocalFile())
            if path.is_file():
                file_paths.append(path)

        if file_paths:
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def add_files(self, image_files: List[ImageFile]):
        """Add image files to the list."""
        for img_file in image_files:
            if img_file not in self.image_files:
                self.image_files.append(img_file)

                # Create list item
                item = QListWidgetItem()

                # Set icon based on format
                if img_file.format:
                    icon = self._get_format_icon(img_file.format)
                    if not icon.isNull():
                        item.setIcon(icon)

                # Create item text
                item_text = f"{img_file.filename}\n{img_file.dimensions_str}  •  {img_file.size_str}"
                item.setText(item_text)

                # Set text alignment
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                self.list_widget.addItem(item)

        self._update_status()
        self._update_empty_state()

    def clear_files(self):
        """Clear all files from the list."""
        self.image_files.clear()
        self.list_widget.clear()
        self._update_status()
        self._update_empty_state()

    def _update_empty_state(self):
        """Toggle between drag hint and file list."""
        if len(self.image_files) == 0:
            self.drag_hint_label.show()
            self.list_widget.hide()
        else:
            self.drag_hint_label.hide()
            self.list_widget.show()

    def get_selected_file(self) -> ImageFile:
        """Get the currently selected image file."""
        current_row = self.list_widget.currentRow()
        if 0 <= current_row < len(self.image_files):
            return self.image_files[current_row]
        return None

    def _update_status(self):
        """Update the status label with file count."""
        count = len(self.image_files)
        self.status_label.setText(f"{count}")

    def set_button_icons(self, add_icon_path: str, clear_icon_path: str):
        """Set icons for Add and Clear buttons."""
        if Path(add_icon_path).exists():
            self.add_btn.setIcon(QIcon(add_icon_path))

        if Path(clear_icon_path).exists():
            self.clear_btn.setIcon(QIcon(clear_icon_path))
