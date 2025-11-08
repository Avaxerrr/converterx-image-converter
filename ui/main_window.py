from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QFileDialog, QStatusBar, QMessageBox, QProgressDialog, QDialog
)
from PySide6.QtCore import Qt, QTimer, QThreadPool, QSettings
from PySide6.QtGui import QShortcut, QKeySequence
from pathlib import Path
from typing import List
import os
import subprocess
import platform

from core.app_settings import AppSettingsController
from core.format_settings import ImageFormat  # NEW: Import for defaults
from models import ImageFile
from ui.app_settings import AppSettingsDialog
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

        # QSettings for persistent window state
        self.settings = QSettings("ConverterX", "ImageConverter")

        # NEW: Create App Settings Controller BEFORE _setup_ui
        self.app_settings = AppSettingsController()
        logger.info("App settings controller initialized", source="MainWindow")

        # NEW: Apply thread pool size setting on startup
        self._apply_threadpool_setting()

        # OUTPUT PREVIEW: Debounce timer (load from settings)
        debounce = self.app_settings.get_out_preview_debounce()
        self.output_preview_debounce_timer = QTimer()
        self.output_preview_debounce_timer.setSingleShot(True)
        self.output_preview_debounce_timer.timeout.connect(self._generate_output_preview)
        self.output_preview_debounce_timer.setInterval(debounce)
        logger.debug(f"Output preview debounce timer initialized ({debounce}ms)", source="MainWindow")

        self._setup_ui()
        self._connect_signals()

        # Restore window geometry and splitter state
        self._restore_window_state()

        # NEW: Apply default quality and format from app settings
        self._apply_default_settings()

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

        # Center panel - Preview (inject controller)
        self.preview = PreviewWidget(controller=self.app_settings, parent=self)
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
        self.file_list.files_removed.connect(self._on_files_removed)

        # Settings signals
        self.settings_panel.settings_changed.connect(self._on_settings_changed)
        self.settings_panel.convert_requested.connect(self._on_convert_selected)

        # NEW: App settings button signal
        self.settings_panel.app_settings_requested.connect(self._open_app_settings)
        logger.debug("App settings button connected", source="MainWindow")

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

            # NEW: Log thread pool status before loading
            self._log_threadpool_status()

            image_files = load_image_files(paths)

            if image_files:
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
        """Handle settings change."""
        self.current_settings = settings

        # If output preview is active, restart debounce timer
        if self.preview.toolbar.output_preview_btn.isChecked():
            logger.debug(
                "Settings changed while output preview active - restarting debounce timer",
                source="MainWindow"
            )
            debounce = self.app_settings.get_out_preview_debounce()
            self.output_preview_debounce_timer.stop()
            self.output_preview_debounce_timer.start(debounce)

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
            # === SINGLE FILE CONVERSION ===
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
            # === BATCH CONVERSION ===
            self._start_batch_conversion(selected_files)

    def _on_conversion_success(self, result: dict):
        """Handle successful conversion."""
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
        if self.log_window is None:
            self.log_window = LogWindow(self)
            logger.info("Log window opened", source="MainWindow")

        # Toggle visibility
        if self.log_window.isVisible():
            self.log_window.hide()
        else:
            self.log_window.show()
            self.log_window.raise_()
            self.log_window.activateWindow()

    def _on_files_dropped(self, file_paths: List[Path]):
        """Handle files dropped into the file list widget."""
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
            first_new_index = len(self.file_list.image_files) - len(loaded_files)
            self.file_list.list_widget.setCurrentRow(first_new_index)

        logger.info(
            f"Added {len(loaded_files)} file(s) via drag and drop",
            source="MainWindow"
        )
        self.status_bar.showMessage(f"Added {len(loaded_files)} file(s)", 2000)

    # ==========================================
    #  OUTPUT PREVIEW METHODS
    # ==========================================

    def _on_output_preview_toggled(self, checked: bool):
        """Handle output preview button toggle."""
        if checked:
            logger.info("Output preview enabled by user", source="MainWindow")

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

            self._generate_output_preview()
        else:
            logger.info("Output preview disabled - reverting to original", source="MainWindow")
            self.output_preview_debounce_timer.stop()

            selected_file = self.file_list.get_selected_file()
            if selected_file:
                self.preview.show_image(selected_file)
                logger.debug(
                    f"Reverted to original preview: {selected_file.filename}",
                    source="MainWindow"
                )

    def _generate_output_preview(self):
        """Generate output preview in worker thread."""
        selected_file = self.file_list.get_selected_file()
        if not selected_file:
            logger.warning("No image selected for preview generation", source="MainWindow")
            return

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

        self.preview.show_loading_overlay("Generating output preview...")
        self.status_bar.showMessage(f"Generating output preview for {selected_file.filename}...")

        worker = OutputPreviewWorker(selected_file.path, self.current_settings)
        worker.signals.finished.connect(self._on_output_preview_ready)
        worker.signals.error.connect(self._on_output_preview_error)
        self.threadpool.start(worker)

        logger.debug("Output preview worker started in thread pool", source="MainWindow")

    def _on_output_preview_ready(self, pixmap):
        """Handle output preview generation complete."""
        logger.success(
            f"Output preview ready: {pixmap.width()}×{pixmap.height()}",
            source="MainWindow"
        )

        self.preview.hide_loading_overlay()
        self.preview.display_output_preview(pixmap)

        selected_file = self.file_list.get_selected_file()
        if selected_file:
            self.status_bar.showMessage(
                f"✓ Output preview ready for {selected_file.filename}",
                3000
            )

    def _on_output_preview_error(self, error_msg: str):
        """Handle output preview generation error."""
        logger.error(f"Output preview generation failed: {error_msg}", source="MainWindow")

        self.preview.hide_loading_overlay()
        self.status_bar.showMessage("✗ Output preview generation failed", 3000)

        QMessageBox.warning(
            self,
            "Preview Error",
            f"Failed to generate output preview:\n\n{error_msg}"
        )

        self.preview.toolbar.output_preview_btn.setChecked(False)

        selected_file = self.file_list.get_selected_file()
        if selected_file:
            self.preview.show_image(selected_file)

    def _restore_window_state(self):
        """Restore window geometry and splitter state from QSettings."""
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
            logger.info("Window geometry restored from settings", source="MainWindow")
        else:
            logger.debug("No saved window geometry found - using defaults", source="MainWindow")

        splitter_state = self.settings.value("window/splitter_state")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)
            logger.info("Splitter state restored from settings", source="MainWindow")
        else:
            logger.debug("No saved splitter state found - using defaults", source="MainWindow")

    def _save_window_state(self):
        """Save window geometry and splitter state to QSettings."""
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/splitter_state", self.main_splitter.saveState())
        logger.info("Window state saved to settings", source="MainWindow")

    def closeEvent(self, event):
        """Override closeEvent to save window state before closing."""
        self._save_window_state()
        event.accept()
        logger.info("Application closing - window state saved", source="MainWindow")

    # ==========================================
    #  BATCH CONVERSION METHODS
    # ==========================================

    def _start_batch_conversion(self, files: List[ImageFile]):
        """Start batch conversion of multiple files."""
        logger.info(f"Starting batch conversion of {len(files)} files", "MainWindow")

        # Snapshot current settings
        settings_snapshot = self.current_settings
        output_folder = self.settings_panel.get_output_folder()

        # Get max workers from app settings
        max_workers = self.app_settings.get_max_concurrent_workers()
        logger.info(f"Batch processor using {max_workers} concurrent workers", "MainWindow")

        # Disable convert button during batch
        self.settings_panel.set_convert_enabled(False)

        # Lazy-create batch window if needed
        if self.batch_window is None:
            self.batch_window = BatchWindow(self)
            logger.debug("Batch window initialized", "MainWindow")

        # FIXED: Always recreate batch processor with current settings
        if self.batch_processor is not None:
            # Disconnect old signals if processor exists
            try:
                self.batch_processor.file_started.disconnect()
                self.batch_processor.file_progress.disconnect()
                self.batch_processor.file_completed.disconnect()
                self.batch_processor.file_failed.disconnect()
                self.batch_processor.batch_finished.disconnect()
            except:
                pass  # Signals might not be connected

        # Create new batch processor with current max_workers
        self.batch_processor = BatchProcessor(max_concurrent=max_workers)
        self._connect_batch_signals()
        logger.debug(f"Batch processor created with max_concurrent={max_workers}", "MainWindow")

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
        """Handle batch conversion completion."""
        # Re-enable convert button
        self.settings_panel.set_convert_enabled(True)

        logger.info(
            f"Batch conversion complete: {successful}/{total} successful, {failed} failed",
            "MainWindow"
        )

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
        if self.batch_window is None:
            self.batch_window = BatchWindow(self)
            logger.debug("Batch window created via Ctrl+B shortcut", "MainWindow")

        if self.batch_window.isVisible():
            self.batch_window.hide()
            logger.debug("Batch window hidden", "MainWindow")
        else:
            self.batch_window.show()
            self.batch_window.raise_()
            self.batch_window.activateWindow()
            logger.debug("Batch window shown", "MainWindow")

    # ==========================================
    #  APP SETTINGS METHODS (NEW)
    # ==========================================

    def _apply_threadpool_setting(self) -> None:
        """
        Apply thread pool size setting to QThreadPool.

        Must be called BEFORE any workers start (in __init__).
        """
        thread_count = self.app_settings.get_threadpool_max_threads()
        QThreadPool.globalInstance().setMaxThreadCount(thread_count)

        logger.info(
            f"Thread pool size set to {thread_count} threads",
            source="MainWindow"
        )

    def _apply_default_settings(self) -> None:
        """
        Apply default quality and format from app settings to settings panel.

        Called once during startup to initialize UI with saved defaults.
        """
        # Get defaults from controller
        default_quality = self.app_settings.get_default_quality()
        default_format = self.app_settings.get_default_output_format()

        # Apply to settings panel widgets
        self.settings_panel.output_widget.quality_slider.setValue(default_quality)

        # Map format enum to combobox index
        format_map = {
            ImageFormat.WEBP: 0,
            ImageFormat.AVIF: 1,
            ImageFormat.JPEG: 2,
            ImageFormat.PNG: 3
        }
        format_index = format_map.get(default_format, 0)
        self.settings_panel.output_widget.format_combo.setCurrentIndex(format_index)

        logger.info(
            f"Default settings applied: {default_format.name} Q{default_quality}",
            source="MainWindow"
        )

    def _log_threadpool_status(self) -> None:
        """Log current thread pool status for debugging."""
        tp = QThreadPool.globalInstance()
        logger.debug(
            f"Thread Pool Status: max={tp.maxThreadCount()}, "
            f"active={tp.activeThreadCount()}",
            source="ThreadPool"
        )

    def _open_app_settings(self) -> None:
        """Open app settings dialog."""
        dialog = AppSettingsDialog(
            controller=self.app_settings,
            parent=self
        )

        if dialog.exec() == QDialog.Accepted:
            self._apply_app_settings()
            logger.info("App settings updated and applied", source="MainWindow")
        else:
            logger.debug("App settings dialog canceled", source="MainWindow")

    def _apply_app_settings(self) -> None:
        """
        Apply changed app settings to running components.

        Some settings apply immediately, others require restart.
        """
        # Apply preview debounce timer (immediate)
        debounce = self.app_settings.get_out_preview_debounce()
        self.output_preview_debounce_timer.setInterval(debounce)
        logger.info(f"Output preview debounce updated to {debounce}ms", source="MainWindow")

        # NEW: Apply thread pool setting (takes effect for new workers)
        thread_count = self.app_settings.get_threadpool_max_threads()
        current_count = QThreadPool.globalInstance().maxThreadCount()

        if thread_count != current_count:
            QThreadPool.globalInstance().setMaxThreadCount(thread_count)
            logger.info(
                f"Thread pool size updated: {current_count} → {thread_count} threads",
                source="MainWindow"
            )

            QMessageBox.information(
                self,
                "Thread Pool Updated",
                f"Thread pool size changed from {current_count} to {thread_count} threads.\n\n"
                "This affects thumbnail generation and preview loading.\n"
                "Change will apply immediately to new operations."
            )
        else:
            logger.debug(f"Thread pool size unchanged ({thread_count} threads)", source="MainWindow")

    def _on_files_removed(self):
        """Handle files being removed from the list."""
        # Clear preview to avoid ghosting effect
        self.preview.clear_preview()
        self.settings_panel.set_convert_enabled(False)
        logger.debug("Files removed - preview cleared", source="MainWindow")
