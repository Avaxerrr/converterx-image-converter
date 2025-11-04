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
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta

from models.image_file import ImageFile
from core.format_settings import ConversionSettings, ImageFormat


class BatchWindow(QDialog):
    """
    Persistent window for batch conversion progress.

    Shows settings snapshot, file list with progress bars,
    overall progress, and status summary.
    """

    # Signal emitted when user requests cancellation
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
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

        # Timer for elapsed time
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self._update_elapsed_time)

        # UI Setup
        self._setup_ui()

        # Override close event (hide instead of destroy)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    def _setup_ui(self):
        """Build the batch window UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Settings Snapshot Header
        self.settings_frame = self._create_settings_header()
        layout.addWidget(self.settings_frame)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator1)

        # Overall Progress Section
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(6)

        self.overall_label = QLabel("Overall Progress: 0/0 files (0%)")
        self.overall_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        progress_layout.addWidget(self.overall_label)

        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setTextVisible(True)
        self.overall_progress.setFixedHeight(24)
        progress_layout.addWidget(self.overall_progress)

        layout.addLayout(progress_layout)

        # File List Table
        self.file_table = self._create_file_table()
        layout.addWidget(self.file_table, 1)  # Stretch factor 1

        # Status Summary Bar
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        # Elapsed/Remaining Time
        self.time_label = QLabel("Elapsed: 00:00:00")
        self.time_label.setStyleSheet("padding: 4px;")
        layout.addWidget(self.time_label)

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel All")
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)

        self.close_btn = QPushButton("Close")
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

        self.settings_label = QLabel("⚙️ Settings: Not set")
        self.settings_label.setStyleSheet("font-weight: 500; font-size: 12px;")
        layout.addWidget(self.settings_label)

        self.output_label = QLabel("📁 Output: Not set")
        self.output_label.setStyleSheet("font-size: 11px; color: #555;")
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
        table.setColumnWidth(3, 100)

        # Table settings
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)

        return table

    def set_settings_snapshot(self, settings: ConversionSettings, output_folder: Path):
        """
        Update settings snapshot display in header.

        Args:
            settings: ConversionSettings snapshot
            output_folder: Output directory path
        """
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
            settings_text = f"⚙️ Settings: {format_str} • {quality_str} • {resize_str} • {size_str}"
        else:
            settings_text = f"⚙️ Settings: {format_str} • {quality_str} • {resize_str}"

        self.settings_label.setText(settings_text)

        # Format output path (truncate if too long)
        output_str = str(output_folder)
        if len(output_str) > 60:
            output_str = "..." + output_str[-57:]
        self.output_label.setText(f"📁 Output: {output_str}")

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
            status_item = QTableWidgetItem("⏳")
            status_item.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 0, status_item)

            # File name
            name_item = QTableWidgetItem(image_file.filename)
            self.file_table.setItem(row, 1, name_item)

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

        # Update status
        self._update_status_summary()

    def update_file_started(self, image_file: ImageFile, current_index: int, total: int):
        """Update file status to 'processing'."""
        if image_file not in self.file_rows:
            return

        row = self.file_rows[image_file]

        # Update status icon
        status_item = self.file_table.item(row, 0)
        status_item.setText("⚙️")

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

        row = self.file_rows[image_file]

        # Update status icon
        status_item = self.file_table.item(row, 0)
        status_item.setText("✅")

        # Update progress bar
        progress_bar = self.file_table.cellWidget(row, 2)
        if progress_bar:
            progress_bar.setValue(100)

        # Update size (saved/increased)
        size_mb = bytes_saved / (1024 * 1024)
        if bytes_saved < 0:
            size_text = f"+{abs(size_mb):.2f} MB"
        else:
            size_text = f"-{size_mb:.2f} MB"

        size_item = self.file_table.item(row, 3)
        size_item.setText(size_text)

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
        status_item.setText("❌")

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
        """
        Handle batch completion.

        Args:
            total: Total files processed
            successful: Successfully converted files
            failed: Failed files
        """
        # Stop timer
        self.elapsed_timer.stop()

        # Disable cancel button, change to "Close"
        self.cancel_btn.setEnabled(False)

        # Update status
        if failed == 0:
            status_text = f"✅ Batch Complete: All {successful} files converted successfully!"
        else:
            status_text = f"⚠️ Batch Complete: {successful} successful, {failed} failed"

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            "padding: 8px; background-color: #d4edda; border-radius: 4px; font-weight: bold;")

    def _update_overall_progress(self):
        """Update overall progress bar and label."""
        processed = self.completed_count + self.failed_count
        percentage = int((processed / self.total_files) * 100) if self.total_files > 0 else 0

        self.overall_progress.setValue(percentage)
        self.overall_label.setText(f"Overall Progress: {processed}/{self.total_files} files ({percentage}%)")

    def _update_status_summary(self):
        """Update status bar with current counts."""
        processing = len([1 for i in range(self.file_table.rowCount())
                          if self.file_table.item(i, 0).text() == "⚙️"])

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
        """Update elapsed time display (called every second)."""
        if self.start_time is None:
            return

        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        self.time_label.setText(f"Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        # Emit signal to BatchProcessor
        self.cancel_requested.emit()

        # Disable button
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelling...")

        # Update status
        self.status_label.setText("⏸️ Cancelling batch... (current files will finish)")

    def closeEvent(self, event):
        """Override close event to hide instead of destroy."""
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