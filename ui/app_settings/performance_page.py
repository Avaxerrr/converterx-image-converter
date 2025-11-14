"""
Performance Settings Page

Settings page for performance-related configuration:
- Max Concurrent Workers (batch processing)
- Thread Pool Size (background tasks)
- Performance Monitor (CPU/RAM display)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController


class PerformanceSettingsPage(QWidget):
    """
    Settings page for performance configuration.

    Controls batch processing workers, thread pool sizing, and performance monitoring.
    """

    def __init__(self, controller: 'AppSettingsController'):
        """
        Initialize performance settings page.

        Args:
            controller: AppSettingsController instance (injected dependency)
        """
        super().__init__()
        self.controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build UI with spinboxes for performance settings."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # ============================================================
        # Title
        # ============================================================
        title = QLabel("Performance Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # ============================================================
        # Max Concurrent Workers
        # ============================================================
        workers_group = QGroupBox("Batch Processing")
        workers_layout = QVBoxLayout()
        workers_layout.setSpacing(8)

        # Label
        workers_label = QLabel("Max Concurrent Workers")
        workers_label.setStyleSheet("font-weight: 500;")

        # Spinbox
        self.workers_spinbox = QSpinBox()
        self.workers_spinbox.setRange(1, 16)
        self.workers_spinbox.setValue(4)
        self.workers_spinbox.setFixedWidth(100)
        self.workers_spinbox.setToolTip(
            "Number of images converted simultaneously.\n"
            "Higher values use more CPU/memory but complete faster.\n"
            "Range: 1-16"
        )

        # Help text
        workers_help = QLabel("Convert up to N images simultaneously in batch mode")
        workers_help.setStyleSheet("color: #858585; font-size: 11px;")
        workers_help.setWordWrap(True)

        workers_layout.addWidget(workers_label)
        workers_layout.addWidget(self.workers_spinbox)
        workers_layout.addWidget(workers_help)
        workers_group.setLayout(workers_layout)
        layout.addWidget(workers_group)

        # ============================================================
        # Thread Pool Size
        # ============================================================
        threads_group = QGroupBox("Thread Management")
        threads_layout = QVBoxLayout()
        threads_layout.setSpacing(8)

        # Label
        threads_label = QLabel("Thread Pool Size")
        threads_label.setStyleSheet("font-weight: 500;")

        # Spinbox
        self.threads_spinbox = QSpinBox()
        self.threads_spinbox.setRange(1, 32)
        self.threads_spinbox.setValue(8)
        self.threads_spinbox.setFixedWidth(100)
        self.threads_spinbox.setToolTip(
            "Maximum threads for thumbnails and previews.\n"
            "Recommended: CPU core count × 2\n"
            "Range: 1-32"
        )

        # Help text
        threads_help = QLabel("Maximum threads for background tasks (thumbnails, previews)")
        threads_help.setStyleSheet("color: #858585; font-size: 11px;")
        threads_help.setWordWrap(True)

        threads_layout.addWidget(threads_label)
        threads_layout.addWidget(self.threads_spinbox)
        threads_layout.addWidget(threads_help)
        threads_group.setLayout(threads_layout)
        layout.addWidget(threads_group)

        # ============================================================
        # Performance Monitor
        # ============================================================
        monitor_group = QGroupBox("Performance Monitoring")
        monitor_layout = QVBoxLayout()
        monitor_layout.setSpacing(12)

        # Enable/disable toggle
        self.show_monitor_checkbox = QCheckBox("Show Performance Monitor")
        self.show_monitor_checkbox.setToolTip(
            "Display CPU and RAM usage in the status bar"
        )
        self.show_monitor_checkbox.stateChanged.connect(self._on_monitor_toggled)
        monitor_layout.addWidget(self.show_monitor_checkbox)

        # Display options container (indented)
        self.display_options_widget = QWidget()
        display_options_layout = QVBoxLayout(self.display_options_widget)
        display_options_layout.setContentsMargins(20, 0, 0, 0)
        display_options_layout.setSpacing(8)

        # Display options label
        display_label = QLabel("Display Options:")
        display_label.setStyleSheet("font-weight: 500; color: #AAAAAA;")
        display_options_layout.addWidget(display_label)

        # Show CPU checkbox
        self.show_cpu_checkbox = QCheckBox("Show CPU Usage")
        self.show_cpu_checkbox.setToolTip("Display CPU percentage in status bar")
        display_options_layout.addWidget(self.show_cpu_checkbox)

        # Show RAM checkbox
        self.show_ram_checkbox = QCheckBox("Show RAM Usage")
        self.show_ram_checkbox.setToolTip("Display memory usage in status bar")
        display_options_layout.addWidget(self.show_ram_checkbox)

        monitor_layout.addWidget(self.display_options_widget)

        # Update interval (indented)
        interval_container = QWidget()
        interval_layout = QHBoxLayout(interval_container)
        interval_layout.setContentsMargins(20, 8, 0, 0)
        interval_layout.setSpacing(8)

        interval_label = QLabel("Update Interval:")
        interval_label.setStyleSheet("font-weight: 500;")
        interval_layout.addWidget(interval_label)

        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 5)
        self.interval_spinbox.setSuffix(" seconds")
        self.interval_spinbox.setFixedWidth(120)
        self.interval_spinbox.setToolTip(
            "How often to refresh performance statistics.\n"
            "Range: 1-5 seconds"
        )
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()

        monitor_layout.addWidget(interval_container)
        self.interval_container = interval_container

        # Help text
        monitor_help = QLabel("Monitor CPU and RAM usage in the status bar")
        monitor_help.setStyleSheet("color: #858585; font-size: 11px;")
        monitor_help.setWordWrap(True)
        monitor_layout.addWidget(monitor_help)

        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        # ============================================================
        # Spacer
        # ============================================================
        layout.addStretch()

    def _on_monitor_toggled(self, state: int) -> None:
        """Handle performance monitor checkbox toggle."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.display_options_widget.setEnabled(enabled)
        self.interval_container.setEnabled(enabled)

    def load_from_controller(self) -> None:
        """Load current settings from controller into UI."""
        # Existing settings
        self.workers_spinbox.setValue(
            self.controller.get_max_concurrent_workers()
        )
        self.threads_spinbox.setValue(
            self.controller.get_threadpool_max_threads()
        )

        # Performance monitor settings
        enabled = self.controller.get_show_performance_monitor()
        self.show_monitor_checkbox.setChecked(enabled)

        self.show_cpu_checkbox.setChecked(
            self.controller.get_performance_show_cpu()
        )
        self.show_ram_checkbox.setChecked(
            self.controller.get_performance_show_ram()
        )

        # Convert milliseconds to seconds for display
        interval_ms = self.controller.get_performance_update_interval()
        self.interval_spinbox.setValue(interval_ms // 1000)

        # Update enabled state of child widgets
        self.display_options_widget.setEnabled(enabled)
        self.interval_container.setEnabled(enabled)

    def save_to_controller(self) -> None:
        """
        Save UI values back to controller.

        Raises:
            ValueError: If validation fails (re-raised from controller)
        """
        # Save existing settings
        self.controller.set_max_concurrent_workers(
            self.workers_spinbox.value()
        )
        self.controller.set_threadpool_max_threads(
            self.threads_spinbox.value()
        )

        # Save performance monitor settings
        self.controller.set_show_performance_monitor(
            self.show_monitor_checkbox.isChecked()
        )
        self.controller.set_performance_show_cpu(
            self.show_cpu_checkbox.isChecked()
        )
        self.controller.set_performance_show_ram(
            self.show_ram_checkbox.isChecked()
        )

        # Convert seconds to milliseconds
        interval_sec = self.interval_spinbox.value()
        self.controller.set_performance_update_interval(interval_sec * 1000)
