"""
Performance Settings Page

Settings page for performance-related configuration:
- Max Concurrent Workers (batch processing)
- Thread Pool Size (background tasks)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController


class PerformanceSettingsPage(QWidget):
    """
    Settings page for performance configuration.

    Controls batch processing workers and thread pool sizing.
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
        # Spacer
        # ============================================================
        layout.addStretch()

    def load_from_controller(self) -> None:
        """Load current settings from controller into UI."""
        self.workers_spinbox.setValue(
            self.controller.get_max_concurrent_workers()
        )
        self.threads_spinbox.setValue(
            self.controller.get_threadpool_max_threads()
        )

    def save_to_controller(self) -> None:
        """
        Save UI values back to controller.

        Raises:
            ValueError: If validation fails (re-raised from controller)
        """
        # Save max concurrent workers
        self.controller.set_max_concurrent_workers(
            self.workers_spinbox.value()
        )

        # Save threadpool max threads
        self.controller.set_threadpool_max_threads(
            self.threads_spinbox.value()
        )
