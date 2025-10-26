from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel
from PySide6.QtCore import Signal
from typing import List
from models.image_file import ImageFile


class FileListWidget(QWidget):
    """Widget displaying the list of images to convert."""

    # Signal emitted when a file is selected
    file_selected = Signal(ImageFile)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_files: List[ImageFile] = []
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title label
        title = QLabel("Files")
        title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(title)

        # File list
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        # Buttons
        self.add_btn = QPushButton("📁 Add Files")
        self.clear_btn = QPushButton("✕ Clear All")

        layout.addWidget(self.add_btn)
        layout.addWidget(self.clear_btn)

        # Status label
        self.status_label = QLabel("No files loaded")
        self.status_label.setStyleSheet("color: #808080; font-size: 9pt;")
        layout.addWidget(self.status_label)

    def add_files(self, image_files: List[ImageFile]):
        """Add image files to the list."""
        for img_file in image_files:
            if img_file not in self.image_files:
                self.image_files.append(img_file)

                # Create list item with file info
                item_text = (
                    f"{img_file.filename}\n"
                    f"  {img_file.dimensions_str}  •  {img_file.size_str}"
                )
                self.list_widget.addItem(item_text)

        self._update_status()

    def clear_files(self):
        """Clear all files from the list."""
        self.image_files.clear()
        self.list_widget.clear()
        self._update_status()

    def get_selected_file(self) -> ImageFile:
        """Get the currently selected image file."""
        current_row = self.list_widget.currentRow()
        if 0 <= current_row < len(self.image_files):
            return self.image_files[current_row]
        return None

    def _on_item_clicked(self):
        """Handle list item click."""
        selected = self.get_selected_file()
        if selected:
            self.file_selected.emit(selected)

    def _update_status(self):
        """Update the status label."""
        count = len(self.image_files)
        if count == 0:
            self.status_label.setText("No files loaded")
        elif count == 1:
            self.status_label.setText("1 file loaded")
        else:
            self.status_label.setText(f"{count} files loaded")
