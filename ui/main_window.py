from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QFileDialog, QStatusBar, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QTimer, QThreadPool, QSettings
from PySide6.QtGui import QShortcut, QKeySequence
from pathlib import Path
from typing import List
import os
import subprocess
import platform

from models import ImageFile
from ui.batch_window import BatchWindow

from ui.log_window import LogWindow
from utils.logger import logger

from ui.file_list_widget import FileListWidget
from ui.preview import PreviewWidget
from ui.settings import SettingsPanel
from utils.file_utils import load_image_files, SUPPORTED_FORMATS
from workers.batch_processor import BatchProcessor
from workers.conversion_worker import ConversionWorker
from core.format_settings import ConversionSettings

from workers.output_preview_worker import OutputPreviewWorker


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.current_settings: ConversionSettings = None
        self.threadpool = QThreadPool()
        self.progress_dialog: QProgressDialog = None

        # Batch processing components (lazy-initialized)
        self.batch_processor = None
        self.batch_window = None

        # Created on-demand log
        self.log_window = None

        # OUTPUT PREVIEW: Debounce timer (500ms delay)
        self.output_preview_debounce_timer = QTimer()
        self.output_preview_debounce_timer.setSingleShot(True)
        self.output_preview_debounce_timer.timeout.connect(self._generate_output_preview)

        # QSettings for persistent window state
        self.settings = QSettings("ConverterX", "ImageConverter")

        logger.debug("Output preview debounce timer initialized (500ms)", source="MainWindow")

        self._setup_ui()
        self._connect_signals()

        # Restore window geometry and splitter state
        self._restore_window_state()

        # Initialize settings from settings panel AFTER signals are connected
        self.current_settings = self.settings_panel.get_settings()
        logger.info(
            f"Initial settings loaded: {self.current_settings.output_format.value} "
            f"Q{self.current_settings.quality}",
            source="MainWindow"
        )

        # logger hotkey
        self._setup_logger_hotkey()

        self._setup_batch_window_shortcut()

        # Test log
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

        # Main splitter (3-way) - store as instance variable for state persistence
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        # Left panel - File list
        self.file_list = FileListWidget()
        self.file_list.setMinimumWidth(250)
        self.main_splitter.addWidget(self.file_list)

        # Center panel - Preview
        self.preview = PreviewWidget()
        self.preview.setMinimumWidth(400)
        self.main_splitter.addWidget(self.preview)

        # Right panel - Settings (includes convert button now)
        self.settings_panel = SettingsPanel()
        self.settings_panel.setMinimumWidth(280)
        self.settings_panel.setMaximumWidth(350)
        self.main_splitter.addWidget(self.settings_panel)

        # Set initial sizes (25/50/25 split)
        self.main_splitter.setSizes([300, 700, 300])

        layout.addWidget(self.main_splitter)

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

        # OUTPUT PREVIEW: Button toggle signal
        self.preview.toolbar.output_preview_toggled.connect(
            self._on_output_preview_toggled
        )

        logger.debug("Output preview signals connected", source="MainWindow")

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
        selected_items = self.file_list.list_widget.selectedItems()
        selected_count = len(selected_items)

        # Enable/disable convert button
        has_selection = selected_count > 0
        self.settings_panel.set_convert_enabled(has_selection)

        # Update convert button text based on selection count
        if selected_count == 0:
            self.settings_panel.convert_btn.setText("Convert")
        elif selected_count == 1:
            self.settings_panel.convert_btn.setText("Convert")
        else:
            self.settings_panel.convert_btn.setText(f"Convert Selected ({selected_count})")

    def _on_settings_changed(self, settings: ConversionSettings):
        """
        Handle settings change.

        MODIFIED: Now triggers output preview regeneration if active.
        """
        self.current_settings = settings

        # If output preview is active, restart debounce timer
        if self.preview.toolbar.output_preview_btn.isChecked():
            logger.debug(
                "Settings changed while output preview active - restarting debounce timer",
                source="MainWindow"
            )
            self.output_preview_debounce_timer.stop()
            self.output_preview_debounce_timer.start(500)  # 500ms delay

    def _on_convert_selected(self):
        """Convert currently selected file(s)."""
        # Get all selected files
        selected_items = self.file_list.list_widget.selectedItems()
        selected_files = []

        for item in selected_items:
            row = self.file_list.list_widget.row(item)
            if row < len(self.file_list.image_files):
                selected_files.append(self.file_list.image_files[row])

        if not selected_files:
            return

        # Check if we have settings
        if not self.current_settings:
            logger.warning("No settings configured", "MainWindow")
            return

        # BRANCH: Single file vs Multiple files
        if len(selected_files) == 1:
            # === SINGLE FILE CONVERSION (EXISTING FLOW) ===
            selected_file = selected_files[0]
            logger.info(
                f"Starting conversion: {selected_file.filename} → "
                f"{self.current_settings.output_format.value} "
                f"(Q{self.current_settings.quality}, "
                f"Resize={self.current_settings.resize_mode.value})",
                "MainWindow"
            )

            # Get output path
            output_folder = self.settings_panel.get_output_folder()
            output_filename = f"{selected_file.path.stem}{self.current_settings.file_extension}"
            output_path = output_folder / output_filename

            # Check if file exists
            if output_path.exists():
                reply = QMessageBox.question(
                    self,
                    "File Exists",
                    f"{output_filename} already exists. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # Disable convert button
            self.settings_panel.set_convert_enabled(False)
            self.status_bar.showMessage(f"Converting {selected_file.filename}...")
            self.status_bar.setStyleSheet("background-color: #0e639c; color: white;")

            # Create and start worker
            worker = ConversionWorker(selected_file, output_path, self.current_settings)
            worker.signals.success.connect(self._on_conversion_success)
            worker.signals.error.connect(self._on_conversion_error)
            worker.signals.finished.connect(self._on_conversion_finished)
            self.threadpool.start(worker)

        else:
            # === BATCH CONVERSION (NEW FLOW) ===
            self._start_batch_conversion(selected_files)

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

        # Create custom message box with buttons
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Conversion Complete")
        msg_box.setIcon(QMessageBox.Information)

        msg_text = (
            f"✓ {result['input_file'].filename} converted successfully!\n\n"
            f"Original: {result['input_file'].size_str}\n"
            f"Converted: {result['output_size'] / 1024:.1f} KB\n"
            f"Savings: {result['savings_string']}\n\n"
            f"Saved to: {result['output_path']}"
        )
        msg_box.setText(msg_text)

        # Add custom buttons
        open_folder_btn = msg_box.addButton("Open Folder", QMessageBox.ActionRole)
        open_image_btn = msg_box.addButton("Open Image", QMessageBox.ActionRole)
        close_btn = msg_box.addButton("Close", QMessageBox.RejectRole)

        # Show dialog and handle button clicks
        msg_box.exec()

        clicked_button = msg_box.clickedButton()

        if clicked_button == open_folder_btn:
            self._open_folder(result['output_path'])
        elif clicked_button == open_image_btn:
            self._open_image(result['output_path'])

        self.status_bar.showMessage(
            f"Converted: {result['savings_string']}", 5000
        )

    def _open_folder(self, file_path: Path):
        """Open the folder containing the file in system file explorer."""
        try:
            folder_path = file_path.parent

            system = platform.system()
            if system == "Windows":
                # Windows: open folder and select file
                subprocess.run(['explorer', '/select,', str(file_path)])
            elif system == "Darwin":  # macOS
                subprocess.run(['open', '-R', str(file_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(folder_path)])

            logger.info(f"Opened folder: {folder_path}", source="MainWindow")
        except Exception as e:
            logger.error(f"Failed to open folder: {e}", source="MainWindow")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not open folder:\n{e}"
            )

    def _open_image(self, file_path: Path):
        """Open the image file with default system application."""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(str(file_path))
            elif system == "Darwin":  # macOS
                subprocess.run(['open', str(file_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(file_path)])

            logger.info(f"Opened image: {file_path.name}", source="MainWindow")
        except Exception as e:
            logger.error(f"Failed to open image: {e}", source="MainWindow")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not open image:\n{e}"
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

    # ==========================================
    #  OUTPUT PREVIEW METHODS (NEW)
    # ==========================================

    def _on_output_preview_toggled(self, checked: bool):
        """
        Handle output preview button toggle.

        Args:
            checked: True if output preview enabled, False if disabled
        """
        if checked:
            # User enabled output preview - generate it
            logger.info("Output preview enabled by user", source="MainWindow")

            # Check if image is selected
            selected_file = self.file_list.get_selected_file()
            if not selected_file:
                logger.warning("No image selected for output preview", source="MainWindow")
                self.preview.toolbar.output_preview_btn.setChecked(False)
                QMessageBox.information(
                    self,
                    "No Image Selected",
                    "Please select an image first to preview output."
                )
                return

            # Generate preview immediately (no debounce on button click)
            self._generate_output_preview()
        else:
            # User disabled output preview - revert to original preview
            logger.info("Output preview disabled - reverting to original", source="MainWindow")

            # Stop any pending preview generation
            self.output_preview_debounce_timer.stop()

            # Reload original preview
            selected_file = self.file_list.get_selected_file()
            if selected_file:
                self.preview.show_image(selected_file)
                logger.debug(
                    f"Reverted to original preview: {selected_file.filename}",
                    source="MainWindow"
                )

    def _generate_output_preview(self):
        """
        Generate output preview in worker thread.

        This method is called either:
        1. Immediately when output preview button is clicked
        2. After 500ms debounce when settings change (if output preview active)
        """
        # Get selected file
        selected_file = self.file_list.get_selected_file()
        if not selected_file:
            logger.warning("No image selected for preview generation", source="MainWindow")
            return

        # Get current settings
        if not self.current_settings:
            logger.warning("No settings configured for preview generation", source="MainWindow")
            return

        logger.info(
            f"Generating output preview for {selected_file.filename} "
            f"(Format: {self.current_settings.output_format.value}, "
            f"Quality: {self.current_settings.quality}, "
            f"Scale: {self.current_settings.resize_percentage}%)",
            source="MainWindow"
        )

        # Show loading overlay
        self.preview.show_loading_overlay("Generating output preview...")

        # Update status bar
        self.status_bar.showMessage(f"Generating output preview for {selected_file.filename}...")

        # Create worker
        worker = OutputPreviewWorker(selected_file.path, self.current_settings)

        # Connect signals
        worker.signals.finished.connect(self._on_output_preview_ready)
        worker.signals.error.connect(self._on_output_preview_error)

        # Start in thread pool (non-blocking)
        self.threadpool.start(worker)

        logger.debug("Output preview worker started in thread pool", source="MainWindow")


        logger.debug("Output preview worker started in thread pool", source="MainWindow")

    def _on_output_preview_ready(self, pixmap):
        """
        Handle output preview generation complete.

        Args:
            pixmap: Generated output preview pixmap
        """
        logger.success(
            f"Output preview ready: {pixmap.width()}×{pixmap.height()}",
            source="MainWindow"
        )

        # Hide loading overlay
        self.preview.hide_loading_overlay()

        # Display in preview widget
        self.preview.display_output_preview(pixmap)

        # Update status bar
        selected_file = self.file_list.get_selected_file()
        if selected_file:
            self.status_bar.showMessage(
                f"✓ Output preview ready for {selected_file.filename}",
                3000
            )

    def _on_output_preview_error(self, error_msg: str):
        """
        Handle output preview generation error.

        Args:
            error_msg: Error message from worker
        """
        logger.error(f"Output preview generation failed: {error_msg}", source="MainWindow")

        # Hide loading overlay
        self.preview.hide_loading_overlay()

        # Update status bar
        self.status_bar.showMessage("✗ Output preview generation failed", 3000)

        # Show error to user
        QMessageBox.warning(
            self,
            "Preview Error",
            f"Failed to generate output preview:\n\n{error_msg}"
        )

        # Uncheck output preview button
        self.preview.toolbar.output_preview_btn.setChecked(False)

        # Revert to original preview
        selected_file = self.file_list.get_selected_file()
        if selected_file:
            self.preview.show_image(selected_file)

    def _restore_window_state(self):
        """
        Restore window geometry and splitter state from QSettings.
        Called once during __init__.
        """
        # Restore window geometry (position + size)
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
            logger.info("Window geometry restored from settings", source="MainWindow")
        else:
            logger.debug("No saved window geometry found - using defaults", source="MainWindow")

        # Restore splitter state
        splitter_state = self.settings.value("window/splitter_state")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)
            logger.info("Splitter state restored from settings", source="MainWindow")
        else:
            logger.debug("No saved splitter state found - using defaults", source="MainWindow")

    def _save_window_state(self):
        """
        Save window geometry and splitter state to QSettings.
        Called when window is closing.
        """
        # Save window geometry (position + size)
        self.settings.setValue("window/geometry", self.saveGeometry())

        # Save splitter state
        self.settings.setValue("window/splitter_state", self.main_splitter.saveState())

        logger.info("Window state saved to settings", source="MainWindow")

    def closeEvent(self, event):
        """
        Override closeEvent to save window state before closing.

        Args:
            event: QCloseEvent
        """
        # Save window state before closing
        self._save_window_state()

        # Accept the close event
        event.accept()

        logger.info("Application closing - window state saved", source="MainWindow")

    def _start_batch_conversion(self, files: List[ImageFile]):
        """
        Start batch conversion of multiple files.

        Args:
            files: List of ImageFile objects to convert
        """
        logger.info(f"Starting batch conversion of {len(files)} files", "MainWindow")

        # Snapshot current settings
        settings_snapshot = self.current_settings
        output_folder = self.settings_panel.get_output_folder()

        # Disable convert button during batch
        self.settings_panel.set_convert_enabled(False)

        # Lazy-create batch window if needed (MUST BE FIRST)
        if self.batch_window is None:
            self.batch_window = BatchWindow(self)
            logger.debug("Batch window initialized", "MainWindow")

        # Lazy-create batch processor if needed (MUST BE SECOND)
        if self.batch_processor is None:
            self.batch_processor = BatchProcessor(self)
            self._connect_batch_signals()  # Safe now because batch_window exists
            logger.debug("Batch processor initialized", "MainWindow")

        # Set settings snapshot in batch window
        self.batch_window.set_settings_snapshot(settings_snapshot, output_folder)

        # Show batch window
        self.batch_window.show()
        self.batch_window.raise_()
        self.batch_window.activateWindow()

        # Start batch in window (populates file list)
        self.batch_window.start_batch(files)

        # Start batch processor
        self.batch_processor.start_batch(files, settings_snapshot, output_folder)

    def _connect_batch_signals(self):
        """Connect BatchProcessor signals to BatchWindow and MainWindow."""
        # Processor → Window
        self.batch_processor.file_started.connect(self.batch_window.update_file_started)
        self.batch_processor.file_progress.connect(self.batch_window.update_file_progress)
        self.batch_processor.file_completed.connect(self.batch_window.update_file_completed)
        self.batch_processor.file_failed.connect(self.batch_window.update_file_failed)
        self.batch_processor.batch_finished.connect(self.batch_window.on_batch_finished)

        # Processor → MainWindow
        self.batch_processor.batch_finished.connect(self._on_batch_finished)

        # Window → Processor
        self.batch_window.cancel_requested.connect(self.batch_processor.cancel_all)
        self.batch_window.pause_requested.connect(self.batch_processor.pause_batch)
        self.batch_window.resume_requested.connect(self.batch_processor.resume_batch)

        logger.debug("Batch signals connected", "MainWindow")

    def _on_batch_finished(self, total: int, successful: int, failed: int):
        """
        Handle batch conversion completion.

        Args:
            total: Total files in batch
            successful: Successfully converted files
            failed: Failed files
        """

        # Re-enable convert button
        self.settings_panel.set_convert_enabled(True)

        # Log summary
        logger.info(
            f"Batch conversion complete: {successful}/{total} successful, {failed} failed",
            "MainWindow"
        )

        # Update status bar
        if failed == 0:
            self.status_bar.showMessage(f"Batch complete: All {successful} files converted successfully!", 5000)
        else:
            self.status_bar.showMessage(f"Batch complete: {successful} successful, {failed} failed", 5000)


    def _setup_batch_window_shortcut(self):
        """Setup Ctrl+B shortcut to toggle batch window."""
        self.batch_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.batch_shortcut.activated.connect(self._toggle_batch_window)

    def _toggle_batch_window(self):
        """Toggle batch window visibility (Ctrl+B handler)."""
        # Lazy-create batch window if it doesn't exist yet
        if self.batch_window is None:
            self.batch_window = BatchWindow(self)
            logger.debug("Batch window created via Ctrl+B shortcut", "MainWindow")

        # Toggle visibility
        if self.batch_window.isVisible():
            self.batch_window.hide()
            logger.debug("Batch window hidden", "MainWindow")
        else:
            self.batch_window.show()
            self.batch_window.raise_()
            self.batch_window.activateWindow()
            logger.debug("Batch window shown", "MainWindow")
