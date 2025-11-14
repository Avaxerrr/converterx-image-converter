"""
Performance Widget

Status bar widget that displays CPU and RAM usage.
Self-contained, listens to app settings for visibility and updates.
"""

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from typing import TYPE_CHECKING

from utils.performance_monitor import PerformanceMonitor
from utils.logger import logger

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController


class PerformanceWidget(QWidget):
    """
    Status bar widget for displaying CPU and RAM usage.

    CPU shows % of total system capacity (0-100%).
    Instant values - responsive to real-time usage spikes.
    """

    def __init__(self, app_settings: 'AppSettingsController', parent=None):
        """
        Initialize performance widget.

        Args:
            app_settings: AppSettingsController instance
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        self.app_settings = app_settings
        self.monitor = PerformanceMonitor()

        self._setup_ui()
        self._setup_timer()
        self._connect_signals()

        # Initial visibility and update
        self._update_visibility()
        self._update_display()

    def _setup_ui(self):
        """Build the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(12)

        # CPU label
        self.cpu_label = QLabel("CPU: --")
        self.cpu_label.setObjectName("performanceCpuLabel")
        layout.addWidget(self.cpu_label)

        # Separator
        self.separator = QLabel("|")
        self.separator.setObjectName("performanceSeparator")
        layout.addWidget(self.separator)

        # RAM label
        self.ram_label = QLabel("RAM: --")
        self.ram_label.setObjectName("performanceRamLabel")
        self.ram_label.setToolTip(
            "Memory usage (RSS - Resident Set Size)\n"
            "May differ slightly from Task Manager (~50-100 MB)"
        )
        layout.addWidget(self.ram_label)

        self.setObjectName("performanceWidget")

    def _setup_timer(self):
        """Setup update timer with precise timing."""
        self.update_timer = QTimer(self)
        self.update_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.update_timer.timeout.connect(self._update_display)

    def _connect_signals(self):
        """Connect to app settings signals."""
        self.app_settings.performance_changed.connect(self._on_settings_changed)

    def _update_visibility(self):
        """Update widget visibility based on settings."""
        enabled = self.app_settings.get_show_performance_monitor()
        show_cpu = self.app_settings.get_performance_show_cpu()
        show_ram = self.app_settings.get_performance_show_ram()

        # Hide entire widget if disabled or both metrics are off
        if not enabled or (not show_cpu and not show_ram):
            self.hide()
            self.update_timer.stop()
            return

        # Show widget
        self.show()

        # Show/hide individual labels
        self.cpu_label.setVisible(show_cpu)
        self.ram_label.setVisible(show_ram)

        # Hide separator if only one metric is shown
        self.separator.setVisible(show_cpu and show_ram)

        # Restart timer with configured interval
        interval = self.app_settings.get_performance_update_interval()
        if self.update_timer.isActive():
            self.update_timer.stop()
        self.update_timer.start(interval)

        logger.debug(
            f"Performance monitor: enabled={enabled}, CPU={show_cpu}, "
            f"RAM={show_ram}, interval={interval}ms, cores={self.monitor.get_cpu_count()}",
            source="PerformanceWidget"
        )

    def _update_display(self):
        """Update displayed CPU and RAM values."""
        if not self.monitor.is_available():
            self.cpu_label.setText("CPU: N/A")
            self.ram_label.setText("RAM: N/A")
            return

        show_cpu = self.app_settings.get_performance_show_cpu()
        show_ram = self.app_settings.get_performance_show_ram()

        # Update CPU (normalized to system capacity, 0-100%, instant value)
        if show_cpu:
            cpu_percent = self.monitor.get_cpu_percent()
            if cpu_percent is not None:
                self.cpu_label.setText(f"CPU: {cpu_percent:.0f}%")

                # Update tooltip with detailed info
                cores_used = self.monitor.get_cpu_cores_utilized()
                total_cores = self.monitor.get_cpu_count()
                if cores_used is not None:
                    tooltip = (
                        f"CPU: {cpu_percent:.1f}% of system capacity\n"
                        f"Using ~{cores_used:.1f} of {total_cores} logical cores\n"
                        f"Real-time value (instant, no smoothing)"
                    )
                    self.cpu_label.setToolTip(tooltip)
            else:
                self.cpu_label.setText("CPU: --")

        # Update RAM
        if show_ram:
            memory_mb = self.monitor.get_memory_mb()
            if memory_mb is not None:
                formatted = PerformanceMonitor.format_memory(memory_mb)
                self.ram_label.setText(f"RAM: {formatted}")
            else:
                self.ram_label.setText("RAM: --")

    def _on_settings_changed(self):
        """Handle app settings change."""
        self._update_visibility()
        # Force immediate update after settings change
        self._update_display()
