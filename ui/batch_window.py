"""
Batch Conversion Window

Persistent window showing batch progress with settings snapshot display.
Hidden (not destroyed) when closed, can be reopened with Ctrl+B.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QProgressBar,
    QHeaderView, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QColor, QIcon
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from models.image_file import ImageFile
from core.format_settings import ConversionSettings
from utils.filename_utils import generate_output_path
from utils.logger import logger


class BatchWindow(QDialog):
    """
    Persistent window for batch conversion progress.

    Shows settings snapshot, file list with progress bars,
    overall progress, and status summary.
    """

    # Signal emitted when user requests cancellation
    cancel_requested = Signal()
    pause_requested = Signal()
    resume_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BatchWindow")
        self.setWindowTitle("Batch Conversion")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)

        # Tracking
        self.file_rows: Dict[ImageFile, int] = {}  # Maps ImageFile to table row
        self.start_time: datetime = None
        self.total_files = 0
        self.completed_count = 0
        self.failed_count = 0
        self.total_saved_bytes = 0

        # Restore window state
        self._restore_window_state()

        # TIME ESTIMATION
        self.file_completion_times: List[float] = []  # Track completion time per file
        self.last_completion_time: Optional[datetime] = None

        # Timer for elapsed time
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self._update_elapsed_time)

        # UI Setup
        self._setup_ui()

        # Override close event (hide instead of destroy)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    def _get_status_icon(self, icon_name: str) -> QIcon:
        """
        Get QIcon from icons folder.

        Args:
            icon_name: Name of icon (e.g., 'pending', 'processing', 'success', 'error')

        Returns:
            QIcon object or empty QIcon if not found
        """
        import os
        from pathlib import Path

        # Map icon names to actual files in your icons folder
        icon_map = {
            'pending': 'schedule.svg',
            'processing': 'cycle.svg',
            'success': 'done_outline.svg',
            'error': 'warning.svg',
            'settings': 'settings.svg',
            'folder': 'folder.svg',
        }

        icon_filename = icon_map.get(icon_name, '')
        if not icon_filename:
            return QIcon()

        # Get absolute path from project root
        # Assumes this file is in ui/ folder and icons/ is at project root
        current_file = Path(__file__)  # batch_window.py location
        project_root = current_file.parent.parent  # Go up to project root
        icon_path = project_root / 'icons' / icon_filename

        if icon_path.exists():
            return QIcon(str(icon_path))
        else:
            # Debug: print the path we're trying to use
            print(f"Icon not found: {icon_path}")
            return QIcon()

    def _setup_ui(self):
        """Build the batch window UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Settings Snapshot Header
        self.settings_frame = self._create_settings_header()
        self.settings_frame.setObjectName("batchSettingsFrame")  # Add object name
        layout.addWidget(self.settings_frame)

        # Overall Progress Section
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(6)

        self.overall_label = QLabel("Overall Progress: 0/0 files (0%)")
        self.overall_label.setObjectName("batchOverallLabel")  # Add object name
        progress_layout.addWidget(self.overall_label)

        self.overall_progress = QProgressBar()
        self.overall_progress.setObjectName("batchOverallProgress")  # Add object name
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setTextVisible(True)
        self.overall_progress.setFixedHeight(24)
        progress_layout.addWidget(self.overall_progress)

        layout.addLayout(progress_layout)

        # File List Table
        self.file_table = self._create_file_table()
        layout.addWidget(self.file_table, 1)

        # Status Summary Bar
        self.status_label = QLabel("Status: Ready")
        self.status_label.setObjectName("batchStatusLabel")  # Add object name
        layout.addWidget(self.status_label)

        # Elapsed/Remaining Time
        self.time_label = QLabel("Elapsed: 00:00:00")
        self.time_label.setObjectName("batchTimeLabel")  # Add object name
        layout.addWidget(self.time_label)

        # Action Buttons (no changes needed)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("pauseButton")
        self.pause_btn.setFixedWidth(120)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)

        self.cancel_btn = QPushButton("Cancel All")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.setFixedWidth(120)
        self.close_btn.clicked.connect(self.hide)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _create_settings_header(self) -> QFrame:
        """Create settings snapshot display header."""
        frame = QFrame()

        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 10, 12, 10)

        self.settings_label = QLabel("Settings: Not set")  # Removed ⚙️ emoji
        self.settings_label.setObjectName("batchSettingsText")
        layout.addWidget(self.settings_label)

        self.output_label = QLabel("Output: Not set")  # Removed 📁 emoji
        self.output_label.setObjectName("batchOutputText")
        layout.addWidget(self.output_label)

        return frame

    def _create_file_table(self) -> QTableWidget:
        """Create file list table with progress bars."""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Status", "File Name", "Progress", "Size"])

        # Column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Status icon
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # File name
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Progress bar
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Size

        table.setColumnWidth(0, 60)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(3, 170)

        # Table settings
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.setIconSize(QSize(20, 20))  # Add icon size

        return table

    def set_settings_snapshot(self, settings: ConversionSettings, output_folder: Path):
        """
        Update settings snapshot display in header.

        Args:
            settings: ConversionSettings snapshot
            output_folder: Output directory path
        """

        # Store for later use
        self.output_folder_path = output_folder

        self.settings_snapshot = settings

        # Format settings text
        format_str = settings.output_format.value

        if settings.lossless:
            quality_str = "Lossless"
        else:
            quality_str = f"Quality {settings.quality}"

        if settings.resize_mode.value == "percentage" and settings.resize_percentage != 100:
            resize_str = f"Resize {settings.resize_percentage:.0f}%"
        else:
            resize_str = "Original size"

        if settings.target_size_kb:
            size_str = f"Target {settings.target_size_kb:.0f} KB"
            settings_text = f"Settings: {format_str} • {quality_str} • {resize_str} • {size_str}"
        else:
            settings_text = f"Settings: {format_str} • {quality_str} • {resize_str}"

        self.settings_label.setText(settings_text)

        # Format output path (truncate if too long)
        output_str = str(output_folder)
        if len(output_str) > 60:
            output_str = "..." + output_str[-57:]
        self.output_label.setText(f"Output: {output_str}")

    def start_batch(self, files: List[ImageFile]):
        """
        Start new batch conversion.

        Args:
            files: List of ImageFile objects to convert
        """
        # Reset state
        self.file_rows.clear()
        self.file_table.setRowCount(0)
        self.total_files = len(files)
        self.completed_count = 0
        self.failed_count = 0
        self.total_saved_bytes = 0

        # Populate file table
        for image_file in files:
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            self.file_rows[image_file] = row

            # Status icon
            status_item = QTableWidgetItem()
            status_item.setIcon(self._get_status_icon('pending'))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 0, status_item)

            # File name
            display_name = self._compute_output_display_name(image_file)
            name_item = QTableWidgetItem(display_name)
            self.file_table.setItem(row, 1, name_item)

            # tooltip with full output path for this file
            try:
                out_path = generate_output_path(image_file, self.settings_snapshot)
                name_item.setToolTip(str(out_path))
            except Exception:
                # silently ignore tooltip if error occurs
                pass

            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            progress_bar.setTextVisible(True)
            progress_bar.setFixedHeight(20)
            self.file_table.setCellWidget(row, 2, progress_bar)

            # Size (empty initially)
            size_item = QTableWidgetItem("...")
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.file_table.setItem(row, 3, size_item)

        # Reset overall progress
        self.overall_progress.setValue(0)
        self.overall_label.setText(f"Overall Progress: 0/{self.total_files} files (0%)")

        # Start timer
        self.start_time = datetime.now()
        self.elapsed_timer.start(1000)  # Update every second

        # Enable cancel button
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel All")
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText("Pause")

        # Update status
        self._update_status_summary()

    def update_file_started(self, image_file: ImageFile, current_index: int, total: int):
        """Update file status to 'processing'."""
        if image_file not in self.file_rows:
            return

        row = self.file_rows[image_file]

        # Update status icon
        status_item = self.file_table.item(row, 0)
        status_item.setIcon(self._get_status_icon('processing'))
        status_item.setText("")  # Clear any text

        # Scroll to current file
        self.file_table.scrollToItem(status_item)

    def update_file_progress(self, image_file: ImageFile, progress: int):
        """Update file progress bar."""
        if image_file not in self.file_rows:
            return

        row = self.file_rows[image_file]
        progress_bar = self.file_table.cellWidget(row, 2)
        if progress_bar:
            progress_bar.setValue(progress)

    def update_file_completed(self, image_file: ImageFile, output_path: Path, bytes_saved: int):
        """Update file status to 'completed'."""
        if image_file not in self.file_rows:
            return

        # Track completion time for ETA calculation
        current_time = datetime.now()
        if self.last_completion_time is not None:
            time_diff = (current_time - self.last_completion_time).total_seconds()
            self.file_completion_times.append(time_diff)
        self.last_completion_time = current_time

        row = self.file_rows[image_file]

        # Update status icon
        status_item = self.file_table.item(row, 0)
        status_item.setIcon(self._get_status_icon('success'))
        status_item.setText("")  # Clear any text

        # Update progress bar
        progress_bar = self.file_table.cellWidget(row, 2)
        if progress_bar:
            progress_bar.setValue(100)

        # Calculate sizes and percentage
        input_size = image_file.size_bytes
        output_size = input_size - bytes_saved

        # Format input size (original)
        if input_size < 1024 * 1000:  # Less than 1000 KB
            input_str = f"{input_size / 1024:.0f} KB"
        else:
            input_str = f"{input_size / (1024 * 1024):.1f} MB"

        # Format output size (converted)
        if output_size < 1024 * 1000:  # Less than 1000 KB
            output_str = f"{output_size / 1024:.0f} KB"
        else:
            output_str = f"{output_size / (1024 * 1024):.1f} MB"

        # Calculate percentage change
        if input_size > 0:
            percent_change = ((input_size - output_size) / input_size) * 100
        else:
            percent_change = 0

        # Format size text with arrow and color
        if bytes_saved > 0:  # File got smaller
            arrow = "↓"
            color = "#28a745"  # Green
            size_text = f"{output_str} ({input_str}) {arrow}{abs(percent_change):.0f}%"
        elif bytes_saved < 0:  # File got bigger
            arrow = "↑"
            color = "#dc3545"  # Red
            size_text = f"{output_str} ({input_str}) {arrow}{abs(percent_change):.0f}%"
        else:  # Same size
            color = "#6c757d"  # Gray
            size_text = f"{output_str} (same)"

        # Update size column
        size_item = self.file_table.item(row, 3)
        size_item.setText(size_text)
        size_item.setForeground(QColor(color))

        # Update tracking
        self.completed_count += 1
        self.total_saved_bytes += bytes_saved

        # Update UI
        self._update_overall_progress()
        self._update_status_summary()

    def update_file_failed(self, image_file: ImageFile, error_message: str):
        """Update file status to 'failed'."""
        if image_file not in self.file_rows:
            return

        row = self.file_rows[image_file]

        # Update status icon
        status_item = self.file_table.item(row, 0)
        status_item.setIcon(self._get_status_icon('error'))
        status_item.setText("")  # Clear any text

        # Update size column with "Failed"
        size_item = self.file_table.item(row, 3)
        size_item.setText("Failed")

        # Set tooltip with error message
        name_item = self.file_table.item(row, 1)
        name_item.setToolTip(f"Error: {error_message}")

        # Update tracking
        self.failed_count += 1

        # Update UI
        self._update_overall_progress()
        self._update_status_summary()

    def on_batch_finished(self, total: int, successful: int, failed: int):
        """Handle batch completion."""
        # Stop timer
        self.elapsed_timer.stop()

        # Disable buttons
        self.cancel_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)

        # Update status with property for styling
        if failed == 0:
            status_text = f"Batch Complete: All {successful} files converted successfully!"
            self.status_label.setProperty("state", "success")
        else:
            status_text = f"Batch Complete: {successful} successful, {failed} failed"
            self.status_label.setProperty("state", "warning")

        self.status_label.setText(status_text)

        # Force style refresh
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        # Show completion dialog
        self._show_completion_dialog(total, successful, failed)

    def _update_overall_progress(self):
        """Update overall progress bar and label."""
        processed = self.completed_count + self.failed_count
        percentage = int((processed / self.total_files) * 100) if self.total_files > 0 else 0

        self.overall_progress.setValue(percentage)
        self.overall_label.setText(f"Overall Progress: {processed}/{self.total_files} files ({percentage}%)")

        # Set property for QSS styling based on state
        if percentage == 100:
            if self.failed_count == 0:
                self.overall_progress.setProperty("state", "success")  # All successful
            elif self.failed_count == self.total_files:
                self.overall_progress.setProperty("state", "error")  # All failed
            else:
                self.overall_progress.setProperty("state", "warning")  # Mixed
        else:
            self.overall_progress.setProperty("state", "processing")  # In progress

        # Force style refresh
        self.overall_progress.style().unpolish(self.overall_progress)
        self.overall_progress.style().polish(self.overall_progress)

    def _update_status_summary(self):
        """Update status bar with current counts."""
        from PySide6.QtCore import QSize

        processing = 0
        for i in range(self.file_table.rowCount()):
            status_item = self.file_table.item(i, 0)
            if status_item and not status_item.icon().isNull():
                # Check if it's the processing icon (you can refine this check)
                processing += 1

        # Calculate total saved
        saved_mb = self.total_saved_bytes / (1024 * 1024)

        status_parts = []
        if processing > 0:
            status_parts.append(f"{processing} processing")
        if self.completed_count > 0:
            status_parts.append(f"{self.completed_count} completed")
        if self.failed_count > 0:
            status_parts.append(f"{self.failed_count} failed")

        status_text = "Status: " + " • ".join(status_parts) if status_parts else "Status: Ready"

        if saved_mb != 0:
            status_text += f" • Total Saved: {saved_mb:.2f} MB"

        self.status_label.setText(status_text)

    def _update_elapsed_time(self):
        """Update elapsed time and ETA display (called every second)."""
        if self.start_time is None:
            return

        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        # Calculate ETA
        eta_str = self._calculate_eta()

        self.time_label.setText(f"Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d} • Remaining: {eta_str}")

    def _calculate_eta(self) -> str:
        """Calculate estimated time remaining."""
        if not self.file_completion_times or self.completed_count == 0:
            return "Calculating..."

        # Average time per file (in seconds)
        avg_time = sum(self.file_completion_times) / len(self.file_completion_times)

        # Files remaining
        remaining_files = self.total_files - (self.completed_count + self.failed_count)

        if remaining_files <= 0:
            return "00:00:00"

        # Estimated seconds remaining
        eta_seconds = int(avg_time * remaining_files)

        hours, remainder = divmod(eta_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"~{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        # Emit signal to BatchProcessor
        self.cancel_requested.emit()

        # Disable button
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelling...")

        # Update status
        self.status_label.setText("Cancelling batch... (current files will finish)")

    def closeEvent(self, event):
        """Override close event to save state and hide instead of destroy."""
        # Save window state
        from PySide6.QtCore import QSettings
        settings = QSettings("ConverterX", "ImageConverter")
        settings.setValue("batch_window/geometry", self.saveGeometry())

        # Hide instead of close
        event.ignore()
        self.hide()

    def toggle_visibility(self):
        """Toggle window visibility (for Ctrl+B shortcut)."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _show_completion_dialog(self, total: int, successful: int, failed: int):
        """Show batch completion summary dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Batch Conversion Complete")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        dialog.setObjectName("batchCompletionDialog")  # Add object name

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)

        # Title
        if failed == 0:
            title_text = "Batch Conversion Complete!"
        else:
            title_text = "Batch Conversion Complete"

        title = QLabel(title_text)
        title.setObjectName("batchDialogTitle")
        title.setProperty("state", "success" if failed == 0 else "warning")
        layout.addWidget(title)

        # Stats
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)

        stats_layout.addWidget(QLabel(f"Successful: {successful} files"))
        if failed > 0:
            stats_layout.addWidget(QLabel(f"Failed: {failed} files"))

        saved_mb = self.total_saved_bytes / (1024 * 1024)
        stats_layout.addWidget(QLabel(f"Total Saved: {saved_mb:.2f} MB"))

        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            stats_layout.addWidget(QLabel(f"Time Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}"))

        layout.addLayout(stats_layout)

        # Buttons (no changes needed - use default button styling)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if failed > 0:
            view_failed_btn = QPushButton("View Failed Files")
            view_failed_btn.clicked.connect(lambda: self._filter_failed_files())
            view_failed_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(view_failed_btn)

        open_folder_btn = QPushButton("Open Output Folder")
        open_folder_btn.clicked.connect(lambda: self._open_output_folder())
        button_layout.addWidget(open_folder_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def _filter_failed_files(self):
        """Scroll to and highlight failed files in table."""
        for row in range(self.file_table.rowCount()):
            status_item = self.file_table.item(row, 0)
            if status_item.text() == "❌":
                self.file_table.selectRow(row)
                self.file_table.scrollToItem(status_item)
                break

    def _open_output_folder(self):
        """Open output folder in file explorer (handles different output modes)."""
        if not hasattr(self, 'output_folder_path'):
            return

        try:
            import subprocess
            import platform

            # Determine which folder to open
            folder_to_open = self.output_folder_path

            # Special handling for "Same as Source" mode
            if str(self.output_folder_path) == "(Same as source files)":
                # Find ANY completed file and open its folder
                if hasattr(self, 'file_rows') and self.file_rows:
                    # Just get the first file from file_rows
                    first_file = next(iter(self.file_rows.keys()), None)
                    if first_file:
                        # Open the folder containing the source file
                        folder_to_open = first_file.path.parent
                        logger.info(f"Using source folder: {folder_to_open}", "BatchWindow")
                    else:
                        logger.warning("No files in file_rows", "BatchWindow")
                        return
                else:
                    logger.warning("No file_rows attribute or empty", "BatchWindow")
                    return

            # Open the folder
            system = platform.system()
            if system == "Windows":
                subprocess.run(['explorer', str(folder_to_open)])
            elif system == "Darwin":  # macOS
                subprocess.run(['open', str(folder_to_open)])
            else:  # Linux
                subprocess.run(['xdg-open', str(folder_to_open)])

            logger.info(f"Opened folder: {folder_to_open}", "BatchWindow")

        except Exception as e:
            logger.error(f"Failed to open output folder: {e}", "BatchWindow")

    def _restore_window_state(self):
        """Restore window size and position from QSettings."""
        from PySide6.QtCore import QSettings
        settings = QSettings("ConverterX", "ImageConverter")

        geometry = settings.value("batch_window/geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def _on_pause_clicked(self):
        """Handle pause/resume button click."""
        # Toggle between pause and resume
        if self.pause_btn.text() == "Pause":
            # Request pause
            self.pause_requested.emit()
            self.pause_btn.setText("Resume")
            self.status_label.setText("Batch paused (active files will finish)")
            logger.debug("Pause requested by user", "BatchWindow")
        else:
            # Request resume
            self.resume_requested.emit()
            self.pause_btn.setText("Pause")
            self._update_status_summary()  # Restore normal status
            logger.debug("Resume requested by user", "BatchWindow")

    def _compute_output_display_name(self, image_file):
        """Compute the final output filename from settings."""
        try:
            if hasattr(self, 'settings_snapshot') and self.settings_snapshot:
                out_path = generate_output_path(image_file, self.settings_snapshot)
                return out_path.name
        except Exception as e:
            logger.warning(f"[BatchWindow] Unable to compute display filename: {e}")
        return image_file.filename
