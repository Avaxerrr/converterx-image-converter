from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QStatusBar, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QTimer, QThreadPool
from PySide6.QtGui import QShortcut, QKeySequence
from pathlib import Path
from typing import List

# Logger
from ui.log_window import LogWindow
from utils.logger import logger, LogLevel

from ui.file_list_widget import FileListWidget
from ui.preview_widget import PreviewWidget
from ui.settings import SettingsPanel
from utils.file_utils import load_image_files, SUPPORTED_FORMATS
from workers.conversion_worker import ConversionWorker
from core.format_settings import ConversionSettings


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.current_settings: ConversionSettings = None
        self.threadpool = QThreadPool()
        self.progress_dialog: QProgressDialog = None

        # Created on-demand log
        self.log_window = None

        self._setup_ui()
        self._connect_signals()

        # logger hotkey
        self._setup_logger_hotkey()

        # ← ADD THIS TEST LOG
        logger.info("ConverterX started successfully", source="App")

        self.file_list.files_dropped.connect(self._on_files_dropped)

    def _setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ConverterX - Image Converter")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main splitter (3-way)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left panel - File list
        self.file_list = FileListWidget()
        self.file_list.setMinimumWidth(250)
        splitter.addWidget(self.file_list)

        # Center panel - Preview
        self.preview = PreviewWidget()
        self.preview.setMinimumWidth(400)
        splitter.addWidget(self.preview)

        # Right panel - Settings (includes convert button now)
        self.settings_panel = SettingsPanel()
        self.settings_panel.setMinimumWidth(280)
        self.settings_panel.setMaximumWidth(350)
        splitter.addWidget(self.settings_panel)

        # Set initial sizes (25/50/25 split)
        splitter.setSizes([300, 700, 300])

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
        self.file_list.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.file_list.files_dropped.connect(self._on_files_dropped)

        # Settings signal
        self.settings_panel.settings_changed.connect(self._on_settings_changed)
        self.settings_panel.convert_requested.connect(self._on_convert_selected)

    def _on_add_files(self):
        """Handle Add Files button click."""
        formats = " ".join([f"*{ext}" for ext in SUPPORTED_FORMATS])
        filter_str = f"Image Files ({formats});;All Files (*.*)"

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            filter_str
        )

        if file_paths:
            paths = [Path(p) for p in file_paths]
            self.status_bar.showMessage("Loading files...")
            image_files = load_image_files(paths)

            if image_files:
                # LOG: User successfully added files to the conversion queue
                logger.info(
                    f"Added {len(image_files)} file(s) to queue",
                    source="MainWindow"
                )
                self.file_list.add_files(image_files)

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
            self.settings_panel.set_convert_enabled(False)
            self.status_bar.showMessage("Files cleared", 2000)

    def _on_file_selected(self, image_file):
        """Handle file selection in list."""
        self.preview.show_image(image_file)
        self.status_bar.showMessage(
            f"Viewing: {image_file.filename}", 2000
        )

        self.settings_panel.set_current_image(image_file)

    def _on_selection_changed(self):
        """Handle selection change."""
        has_selection = len(self.file_list.list_widget.selectedItems()) > 0
        self.settings_panel.set_convert_enabled(has_selection)

    def _on_settings_changed(self, settings: ConversionSettings):
        """Handle settings change."""
        self.current_settings = settings

    def _on_convert_selected(self):
        """Convert currently selected file."""
        selected_file = self.file_list.get_selected_file()

        # LOG: User initiated conversion - log settings for debugging
        if selected_file and self.current_settings:
            logger.info(
                f"Starting conversion: {selected_file.filename} → "
                f"{self.current_settings.output_format.value} "
                f"(Q{self.current_settings.quality}, "
                f"Resize:{self.current_settings.resize_mode.value})",
                source="MainWindow"
            )

        if not selected_file:
            return

        if not self.current_settings:
            QMessageBox.warning(self, "No Settings", "Please configure output settings first.")
            return

        output_folder = self.settings_panel.get_output_folder()
        output_filename = selected_file.path.stem + self.current_settings.file_extension
        output_path = output_folder / output_filename

        if output_path.exists():
            reply = QMessageBox.question(
                self, "File Exists",
                f"{output_filename} already exists. Overwrite?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # Show progress in status bar
        self.settings_panel.set_convert_enabled(False)
        self.status_bar.showMessage(f"⏳ Converting {selected_file.filename}...")
        self.status_bar.setStyleSheet("background-color: #0e639c; color: white;")

        # Create and start worker
        worker = ConversionWorker(selected_file, output_path, self.current_settings)
        worker.signals.success.connect(self._on_conversion_success)
        worker.signals.error.connect(self._on_conversion_error)
        worker.signals.finished.connect(self._on_conversion_finished)

        self.threadpool.start(worker)

    def _on_conversion_success(self, result: dict):
        """Handle successful conversion."""
        # LOG: Successful conversion with file sizes and savings
        logger.success(
            f"✓ {result['input_file'].filename} → "
            f"{result['output_path'].name} "
            f"({result['input_file'].size_str} → {result['output_size'] / 1024:.1f} KB, "
            f"{result['savings_string']})",
            source="Converter"
        )
        if self.progress_dialog:
            self.progress_dialog.close()

        msg = (
            f"✓ {result['input_file'].filename} converted successfully!\n\n"
            f"Original: {result['input_file'].size_str}\n"
            f"Converted: {result['output_size'] / 1024:.1f} KB\n"
            f"Savings: {result['savings_string']}\n\n"
            f"Saved to: {result['output_path']}"
        )

        QMessageBox.information(self, "Conversion Complete", msg)
        self.status_bar.showMessage(
            f"Converted: {result['savings_string']}", 5000
        )

    def _on_conversion_error(self, error_msg: str):
        """Handle conversion error."""
        # LOG: Conversion failed - critical for debugging user issues
        logger.error(f"Conversion failed: {error_msg}", source="Converter")
        if self.progress_dialog:
            self.progress_dialog.close()

        QMessageBox.critical(self, "Conversion Failed", error_msg)
        self.status_bar.showMessage("Conversion failed", 3000)

    def _on_conversion_finished(self):
        """Handle conversion completion."""
        self.settings_panel.set_convert_enabled(True)
        self.status_bar.setStyleSheet("")  # Reset status bar color

    def _setup_logger_hotkey(self):
        """Setup F12 hotkey to toggle log window."""
        self.log_shortcut = QShortcut(QKeySequence("F12"), self)
        self.log_shortcut.activated.connect(self._toggle_log_window)

    def _toggle_log_window(self):
        """Show/hide log window."""
        print("F12 pressed - toggling log window")  # ← ADD THIS FOR DEBUGGING

        if self.log_window is None:
            print("Creating new log window")  # ← ADD THIS
            self.log_window = LogWindow(self)
            logger.info("Log window opened", source="MainWindow")

        # Toggle visibility
        if self.log_window.isVisible():
            print("Hiding log window")  # ← ADD THIS
            self.log_window.hide()
        else:
            print("Showing log window")  # ← ADD THIS
            self.log_window.show()
            self.log_window.raise_()
            self.log_window.activateWindow()

    def _on_files_dropped(self, file_paths: List[Path]):
        """Handle files dropped into the file list widget."""
        from utils.file_utils import load_image_files

        self.status_bar.showMessage("Loading dropped files...")
        loaded_files = load_image_files(file_paths)

        if not loaded_files:
            QMessageBox.warning(
                self,
                "No Valid Images",
                "None of the dropped files are supported image formats."
            )
            self.status_bar.showMessage("No valid images", 2000)
            return

        # Add to file list
        self.file_list.add_files(loaded_files)

        # Select the first newly added file to show preview
        if loaded_files:
            # Calculate the index of the first newly added file
            first_new_index = len(self.file_list.image_files) - len(loaded_files)
            self.file_list.list_widget.setCurrentRow(first_new_index)

        # Log success using the correct logger method
        logger.info(
            f"Added {len(loaded_files)} file(s) via drag and drop",
            source="MainWindow"
        )
        self.status_bar.showMessage(f"Added {len(loaded_files)} file(s)", 2000)
