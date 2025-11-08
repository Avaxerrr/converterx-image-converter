from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QListWidgetItem, QSizePolicy, QMenu, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt, QSize, QThreadPool
from PySide6.QtGui import QIcon, QPixmap, QAction
from typing import List, Dict
from pathlib import Path
import subprocess
import platform
import os
from models.image_file import ImageFile
from workers.thumbnail_generator import ThumbnailGenerator


class FileListWidget(QWidget):
    """Widget displaying the list of images to convert."""

    # Signals
    file_selected = Signal(ImageFile)
    files_dropped = Signal(list)  # Emits List[Path]
    files_removed = Signal()  # Signal when files are removed
    files_dropped = Signal(list)  # Emits List[Path]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_files: List[ImageFile] = []
        self.threadpool = QThreadPool()  # For async thumbnail generation
        self.thumbnail_cache: Dict[Path, QPixmap] = {}  # Cache thumbnails by file path
        self._setup_ui()

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Enable context menu
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 8, 8)
        layout.setSpacing(8)

        # Header with title and status count
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.title_label = QLabel("Files")
        self.title_label.setObjectName("titleLabel")
        header_layout.addWidget(self.title_label)

        self.status_label = QLabel("0")
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Drag & drop hint label (shown when empty)
        self.drag_hint_label = QLabel("Drag & drop images here\nor click 'Add files'")
        self.drag_hint_label.setObjectName("dragHintLabel")
        self.drag_hint_label.setAlignment(Qt.AlignCenter)
        self.drag_hint_label.setWordWrap(True)
        self.drag_hint_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.drag_hint_label)

        # File list with optimized settings
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("fileListWidget")
        thumb_max_height = ThumbnailGenerator.MAX_HEIGHT
        thumb_max_width = ThumbnailGenerator.MAX_WIDTH  # Max width x height for thumbnails
        self.list_widget.setIconSize(QSize(thumb_max_width, thumb_max_height))
        self.list_widget.setSpacing(4)
        self.list_widget.setWordWrap(False)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.setSelectionBehavior(QAbstractItemView.SelectItems)

        # Connect signals
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(self.list_widget)

        # Initially show hint, hide list
        self.list_widget.hide()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.add_btn = QPushButton("Add files")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setMinimumHeight(32)

        self.clear_btn = QPushButton("Clear files")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setMinimumHeight(32)

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
        """Add image files to the list with async thumbnail generation."""
        for img_file in image_files:
            if img_file not in self.image_files:
                row_index = len(self.image_files)
                self.image_files.append(img_file)

                # Create list item WITHOUT icon initially
                item = QListWidgetItem()
                item_text = f"{img_file.filename}\n{img_file.dimensions_str}  •  {img_file.size_str}"
                item.setText(item_text)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                # Check if thumbnail is already cached
                if img_file.path in self.thumbnail_cache:
                    # Reuse cached thumbnail - instant!
                    item.setIcon(QIcon(self.thumbnail_cache[img_file.path]))
                else:
                    # Generate thumbnail asynchronously only if not cached
                    self._generate_thumbnail_async(img_file.path, row_index)

                self.list_widget.addItem(item)

        self._update_status()
        self._update_empty_state()

    def _generate_thumbnail_async(self, image_path: Path, row_index: int):
        """Start async thumbnail generation for an image."""
        worker = ThumbnailGenerator(image_path, row_index)
        worker.signals.finished.connect(self._on_thumbnail_ready)
        worker.signals.error.connect(self._on_thumbnail_error)
        self.threadpool.start(worker)

    def _on_thumbnail_ready(self, row_index: int, thumbnail: QPixmap):
        """Handle thumbnail generation completion."""
        if 0 <= row_index < self.list_widget.count():
            item = self.list_widget.item(row_index)
            if item and row_index < len(self.image_files):
                # Cache the thumbnail for future reuse
                image_path = self.image_files[row_index].path
                self.thumbnail_cache[image_path] = thumbnail

                # Set the icon
                item.setIcon(QIcon(thumbnail))

    def _on_thumbnail_error(self, row_index: int, error_msg: str):
        """Handle thumbnail generation error - item stays without icon."""
        print(f"Thumbnail error for row {row_index}: {error_msg}")

    def clear_files(self):
        """Clear all files from the list."""
        self.image_files.clear()
        self.list_widget.clear()
        self.thumbnail_cache.clear()
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

    def _show_context_menu(self, position):
        """Show context menu on right-click."""
        # Get the item at the clicked position
        item = self.list_widget.itemAt(position)

        if not item:
            return  # No item clicked, don't show menu

        # Get the corresponding image file
        row = self.list_widget.row(item)
        if row < 0 or row >= len(self.image_files):
            return

        image_file = self.image_files[row]

        # Create context menu
        menu = QMenu(self)

        # Get count of selected items
        selected_items = self.list_widget.selectedItems()
        selected_count = len(selected_items)

        # Add "Open Folder Location" action
        open_folder_action = QAction("Open Folder Location", self)
        open_folder_action.triggered.connect(lambda: self._open_folder_location(image_file))
        menu.addAction(open_folder_action)

        # Add "Edit" action (placeholder)
        edit_action = QAction("Edit Photo", self)
        edit_action.triggered.connect(lambda: self._edit_image(image_file))
        menu.addAction(edit_action)

        # Add separator
        menu.addSeparator()

        # Add "Remove" action with dynamic text
        if selected_count > 1:
            remove_action = QAction(f"Remove {selected_count} Images", self)
            remove_action.triggered.connect(self._remove_selected_files)
        else:
            remove_action = QAction("Remove Image", self)
            remove_action.triggered.connect(lambda: self._remove_single_file(row))

        menu.addAction(remove_action)

        # Show menu at cursor position
        menu.exec(self.list_widget.mapToGlobal(position))

    def _remove_single_file(self, row: int):
        """Remove a single file from the list."""
        if 0 <= row < len(self.image_files):
            removed_file = self.image_files.pop(row)
            self.list_widget.takeItem(row)
            self._update_status()
            self._update_empty_state()
            print(f"Removed: {removed_file.filename}")

    def _remove_selected_files(self):
        """Remove all selected files from the list (instant removal like clear_files)."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        # Get indices of selected items
        selected_indices = set(self.list_widget.row(item) for item in selected_items)
        removed_count = len(selected_indices)

        # Create new lists excluding selected items (same strategy as clear_files)
        new_image_files = [
            img for idx, img in enumerate(self.image_files)
            if idx not in selected_indices
        ]

        # Rebuild the list widget from scratch (same as clear_files)
        self.list_widget.clear()
        self.image_files.clear()

        # Emit signal to notify that files were removed
        self.files_removed.emit()

        # Re-add remaining items
        if new_image_files:
            self.add_files(new_image_files)
        else:
            self._update_status()
            self._update_empty_state()

        print(f"Removed {removed_count} file(s)")

    def _open_folder_location(self, image_file: ImageFile):
        """Open the folder containing the image file."""
        try:
            file_path = image_file.path

            system = platform.system()
            if system == "Windows":
                # Windows: open folder and select file
                subprocess.run(['explorer', '/select,', str(file_path)])
            elif system == "Darwin":  # macOS
                subprocess.run(['open', '-R', str(file_path)])
            else:  # Linux
                folder_path = file_path.parent
                subprocess.run(['xdg-open', str(folder_path)])

            print(f"Opened folder for: {image_file.filename}")
        except Exception as e:
            print(f"Failed to open folder: {e}")

    def _edit_image(self, image_file: ImageFile):
        """Edit image - placeholder for future implementation."""
        print(f"Edit action triggered for: {image_file.filename}")
        # TODO: Implement edit functionality
        # This could open an external editor or internal editing dialog
