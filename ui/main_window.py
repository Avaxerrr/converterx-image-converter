from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QFileDialog, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt
from pathlib import Path
from typing import List

from ui.file_list_widget import FileListWidget
from ui.preview_widget import PreviewWidget
from utils.file_utils import load_image_files, SUPPORTED_FORMATS


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ConverterX - Image Converter")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)

        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left panel - File list
        self.file_list = FileListWidget()
        self.file_list.setMinimumWidth(250)
        splitter.addWidget(self.file_list)

        # Right panel - Preview
        self.preview = PreviewWidget()
        self.preview.setMinimumWidth(400)
        splitter.addWidget(self.preview)

        # Set initial sizes (30/70 split for 1000px)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        """Connect widget signals to slots."""
        self.file_list.add_btn.clicked.connect(self._on_add_files)
        self.file_list.clear_btn.clicked.connect(self._on_clear_files)
        self.file_list.file_selected.connect(self._on_file_selected)

    def _on_add_files(self):
        """Handle Add Files button click."""
        # Create filter string for supported formats
        formats = " ".join([f"*{ext}" for ext in SUPPORTED_FORMATS])
        filter_str = f"Image Files ({formats});;All Files (*.*)"

        # Open file dialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            filter_str
        )

        if file_paths:
            # Convert to Path objects
            paths = [Path(p) for p in file_paths]

            # Load image files
            self.status_bar.showMessage("Loading files...")
            image_files = load_image_files(paths)

            if image_files:
                self.file_list.add_files(image_files)
                self.status_bar.showMessage(
                    f"Loaded {len(image_files)} file(s)", 3000
                )
            else:
                self.status_bar.showMessage("No valid images found", 3000)

    def _on_clear_files(self):
        """Handle Clear All button click."""
        if not self.file_list.image_files:
            return

        reply = QMessageBox.question(
            self,
            "Clear Files",
            "Remove all files from the list?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.file_list.clear_files()
            self.preview.clear_preview()
            self.status_bar.showMessage("Files cleared", 2000)

    def _on_file_selected(self, image_file):
        """Handle file selection in list."""
        self.preview.show_image(image_file)
        self.status_bar.showMessage(
            f"Viewing: {image_file.filename}", 2000
        )
