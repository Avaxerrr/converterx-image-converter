"""
Log viewer window with filtering and controls.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QCheckBox, QGroupBox, QLabel
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from pathlib import Path
from utils.logger import logger, LogLevel, LogMessage


class LogWindow(QDialog):
    """Window for displaying application logs with filtering options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Log")
        self.setMinimumSize(500, 200)
        self._setup_ui()
        self._load_stylesheet()

        # Register callback with logger
        logger.add_callback(self._on_new_log_message)

        # Auto-scroll enabled by default
        self._auto_scroll = True

        # Load existing messages
        self._load_existing_messages()

    def _load_stylesheet(self):
        """Load the stylesheet from external QSS file."""
        style_file = Path(__file__).parent.parent / "qss" / "log_window.qss"

        if style_file.exists():
            with open(style_file, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Filter controls at top
        filter_group = QGroupBox("Filter Log Levels")
        filter_group.setObjectName("filterGroup")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)

        # Checkboxes for each log level
        self.filter_debug = QCheckBox("Debug")
        self.filter_debug.setObjectName("filterCheckbox")
        self.filter_debug.setChecked(True)
        self.filter_debug.stateChanged.connect(self._refresh_display)

        self.filter_info = QCheckBox("Info")
        self.filter_info.setObjectName("filterCheckbox")
        self.filter_info.setChecked(True)
        self.filter_info.stateChanged.connect(self._refresh_display)

        self.filter_success = QCheckBox("Success")
        self.filter_success.setObjectName("filterCheckbox")
        self.filter_success.setChecked(True)
        self.filter_success.stateChanged.connect(self._refresh_display)

        self.filter_warning = QCheckBox("Warning")
        self.filter_warning.setObjectName("filterCheckbox")
        self.filter_warning.setChecked(True)
        self.filter_warning.stateChanged.connect(self._refresh_display)

        self.filter_error = QCheckBox("Error")
        self.filter_error.setObjectName("filterCheckbox")
        self.filter_error.setChecked(True)
        self.filter_error.stateChanged.connect(self._refresh_display)

        filter_layout.addWidget(self.filter_debug)
        filter_layout.addWidget(self.filter_info)
        filter_layout.addWidget(self.filter_success)
        filter_layout.addWidget(self.filter_warning)
        filter_layout.addWidget(self.filter_error)
        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # Log display area
        self.log_display = QTextEdit()
        self.log_display.setObjectName("logDisplay")
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_display)

        # Bottom controls
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setObjectName("autoScrollCheckbox")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.stateChanged.connect(self._on_auto_scroll_changed)
        bottom_layout.addWidget(self.auto_scroll_cb)

        # Message count label
        self.count_label = QLabel("0 messages")
        self.count_label.setObjectName("countLabel")
        bottom_layout.addWidget(self.count_label)

        bottom_layout.addStretch()

        # Action buttons
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setObjectName("actionButton")
        self.copy_btn.clicked.connect(self._copy_to_clipboard)

        self.save_btn = QPushButton("Save to File")
        self.save_btn.setObjectName("actionButton")
        self.save_btn.clicked.connect(self._save_to_file)

        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self._clear_log)

        bottom_layout.addWidget(self.copy_btn)
        bottom_layout.addWidget(self.save_btn)
        bottom_layout.addWidget(self.clear_btn)

        layout.addLayout(bottom_layout)

    def _load_existing_messages(self):
        """Load existing messages from logger."""
        messages = logger.get_messages()
        for msg in messages:
            self._append_message(msg)
        self._update_count()

    def _on_new_log_message(self, message: LogMessage):
        """Callback when new message is logged."""
        # Use QTimer to safely update UI from any thread
        QTimer.singleShot(0, lambda: self._append_message(message))

    def _append_message(self, message: LogMessage):
        """Append a message to the display if it passes filters."""
        if not self._should_show_level(message.level):
            return

        # Move cursor to end
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Set color based on level
        format = QTextCharFormat()
        format.setForeground(self._get_color_for_level(message.level))

        cursor.setCharFormat(format)
        cursor.insertText(str(message) + "\n")

        # Auto-scroll if enabled
        if self._auto_scroll:
            self.log_display.ensureCursorVisible()

        self._update_count()

    def _should_show_level(self, level: LogLevel) -> bool:
        """Check if a log level should be displayed based on filters."""
        if level == LogLevel.DEBUG:
            return self.filter_debug.isChecked()
        elif level == LogLevel.INFO:
            return self.filter_info.isChecked()
        elif level == LogLevel.SUCCESS:
            return self.filter_success.isChecked()
        elif level == LogLevel.WARNING:
            return self.filter_warning.isChecked()
        elif level == LogLevel.ERROR:
            return self.filter_error.isChecked()
        return True

    def _get_color_for_level(self, level: LogLevel) -> QColor:
        """Get display color for log level."""
        colors = {
            LogLevel.DEBUG: QColor(150, 150, 150),    # Gray
            LogLevel.INFO: QColor(100, 180, 255),     # Blue
            LogLevel.SUCCESS: QColor(100, 220, 100),  # Green
            LogLevel.WARNING: QColor(255, 200, 80),   # Orange
            LogLevel.ERROR: QColor(255, 100, 100),    # Red
        }
        return colors.get(level, QColor(255, 255, 255))

    def _refresh_display(self):
        """Refresh the display with current filters."""
        self.log_display.clear()
        messages = logger.get_messages()
        for msg in messages:
            self._append_message(msg)
        self._update_count()

    def _update_count(self):
        """Update the message count label."""
        visible_count = self.log_display.document().blockCount() - 1  # -1 for empty line at end
        total_count = len(logger.get_messages())
        self.count_label.setText(f"{visible_count} / {total_count} messages")

    def _on_auto_scroll_changed(self, state):
        """Handle auto-scroll checkbox change."""
        self._auto_scroll = state == Qt.Checked

    def _copy_to_clipboard(self):
        """Copy log contents to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_display.toPlainText())
        logger.info("Log copied to clipboard", "LogWindow")

    def _save_to_file(self):
        """Save log to a text file."""
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime

        default_name = f"converterx_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log File",
            str(Path.home() / default_name),
            "Text Files (*.txt);;All Files (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_display.toPlainText())
                logger.success(f"Log saved to {file_path}", "LogWindow")
            except Exception as e:
                logger.error(f"Failed to save log: {e}", "LogWindow")

    def _clear_log(self):
        """Clear the log display and logger."""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Clear Log",
            "Are you sure you want to clear all log messages?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logger.clear()
            self.log_display.clear()
            self._update_count()

    def closeEvent(self, event):
        """Handle window close event."""
        # Unregister callback when window closes
        logger.remove_callback(self._on_new_log_message)
        event.accept()
