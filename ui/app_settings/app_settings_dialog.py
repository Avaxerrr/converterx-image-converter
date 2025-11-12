"""
App Settings Dialog

Main dialog window with sidebar navigation for app settings.
Takes AppSettingsController via dependency injection (constructor parameter).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QStackedWidget, QPushButton, QMessageBox, QScrollArea, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController


class AppSettingsDialog(QDialog):
    """
    App settings dialog with sidebar navigation.

    NOT responsible for creating controller - it's injected via constructor.
    This follows dependency injection pattern used throughout the app.

    Usage:
        controller = AppSettingsController()
        dialog = AppSettingsDialog(controller=controller, parent=main_window)
        if dialog.exec() == QDialog.Accepted:
            # Settings were saved
    """

    def __init__(self, controller: 'AppSettingsController', parent=None):
        """
        Initialize app settings dialog.

        Args:
            controller: AppSettingsController instance (injected dependency)
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        self.controller = controller

        # Setup window
        self.setWindowTitle("App Settings")
        self.setMinimumSize(500, 500)
        self.resize(700, 500)
        self.setModal(True)

        # Build UI
        self._setup_ui()
        self._create_pages()
        self._load_all_pages()
        self._setup_shortcuts()

    def _setup_ui(self) -> None:
        """Build dialog layout with sidebar and content area."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ============================================================
        # Content Area: Sidebar + Pages (Scrollable)
        # ============================================================
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar (QListWidget)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setObjectName("settingsSidebar")
        self.sidebar.currentRowChanged.connect(self._on_page_changed)
        self.sidebar.setFocusPolicy(Qt.NoFocus)
        self.sidebar.setAttribute(Qt.WA_MacShowFocusRect, False)

        # Wrap content in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setObjectName("settingsScrollArea")

        # Content area (QStackedWidget)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("settingsContent")
        scroll_area.setWidget(self.content_stack)

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(scroll_area)
        main_layout.addLayout(content_layout)

        # ============================================================
        # Bottom Button Bar
        # ============================================================
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(16, 16, 16, 16)
        button_layout.setSpacing(8)

        # Restore Defaults button (left side)
        self.restore_btn = QPushButton("Restore Defaults")
        self.restore_btn.setObjectName("restoreDefaultsBtn")
        self.restore_btn.clicked.connect(self._on_restore_defaults)

        # Right side buttons: Apply, OK, Cancel
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("applyBtn")
        self.apply_btn.clicked.connect(self._on_apply)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_ok)

        # Add buttons to layout
        button_layout.addWidget(self.restore_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.ok_btn)

        main_layout.addLayout(button_layout)

    def _create_pages(self) -> None:
        """Create settings pages and add to sidebar/stack."""
        from .performance_page import PerformanceSettingsPage
        from .preview_page import PreviewSettingsPage
        from .defaults_page import DefaultSettingsPage
        from PySide6.QtWidgets import QScrollArea

        # Import documentation pages
        from .about_page import AboutPage
        from .base_doc_page import QuickGuidePage, FeaturesPage

        # Create settings pages and STORE REFERENCES
        self.performance_page = PerformanceSettingsPage(self.controller)
        self.preview_page = PreviewSettingsPage(self.controller)
        self.defaults_page = DefaultSettingsPage(self.controller)

        # Create documentation pages (read-only, no settings)
        self.about_page = AboutPage(self.controller)
        self.quick_guide_page = QuickGuidePage(self.controller)
        self.features_page = FeaturesPage(self.controller)

        # Store which pages have settings (for save operations)
        self.settings_pages = [
            self.performance_page,
            self.preview_page,
            self.defaults_page
        ]

        # Helper function to wrap page in scroll area
        def create_scrollable_page(page_widget):
            """Wrap a page widget in a scroll area."""
            scroll = QScrollArea()
            scroll.setWidget(page_widget)
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setFrameShape(QScrollArea.NoFrame)
            return scroll

        # Wrap each settings page
        performance_scroll = create_scrollable_page(self.performance_page)
        preview_scroll = create_scrollable_page(self.preview_page)
        defaults_scroll = create_scrollable_page(self.defaults_page)

        # Define all pages with icons and titles
        # (is_header, title, page_widget, icon_path)
        pages = [
            # Settings Section
            (True, "SETTINGS", None, None),
            (False, "Performance", performance_scroll, ":/icons/performance-settings.svg"),
            (False, "Preview", preview_scroll, ":/icons/preview-settings.svg"),
            (False, "Defaults", defaults_scroll, ":/icons/default-settings.svg"),

            # About & Documentation Section
            (True, "ABOUT & DOCS", None, None),
            (False, "About", self.about_page, ":/icons/about.svg"),
            (False, "Quick Guide", self.quick_guide_page, ":/icons/quick-guide.svg"),
            (False, "Features", self.features_page, ":/icons/features.svg"),
        ]

        # Add to UI
        for is_header, title, page_widget, icon_path in pages:
            if is_header:
                # Create section header
                item = QListWidgetItem(title)
                item.setFlags(Qt.ItemFlag.NoItemFlags)  # Non-selectable
                item.setForeground(Qt.GlobalColor.darkGray)
                font = item.font()
                font.setPointSize(9)
                font.setBold(True)
                item.setFont(font)
                self.sidebar.addItem(item)
            else:
                # Create regular page item
                item = QListWidgetItem(QIcon(icon_path), title)
                self.sidebar.addItem(item)
                self.content_stack.addWidget(page_widget)

        # Select first actual page (index 1, skip "SETTINGS" header)
        self.sidebar.setCurrentRow(1)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for dialog."""
        # Ctrl+Return / Cmd+Return to apply and close (OK)
        ok_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        ok_shortcut.activated.connect(self._on_ok)

        # Escape to cancel
        cancel_shortcut = QShortcut(QKeySequence("Esc"), self)
        cancel_shortcut.activated.connect(self.reject)

    def _on_page_changed(self, index: int) -> None:
        """
        Handle sidebar selection change.

        Accounts for section headers which don't have corresponding pages.

        Args:
            index: Index of selected sidebar item in sidebar
        """
        # Section headers are at indices 0 (SETTINGS) and 4 (ABOUT & DOCS)
        # We need to map sidebar index to content_stack index

        # Calculate actual page index by subtracting headers before this item
        page_index = index
        if index > 0:  # After "SETTINGS" header
            page_index -= 1
        if index > 4:  # After "ABOUT & DOCS" header
            page_index -= 1

        if page_index >= 0:
            self.content_stack.setCurrentIndex(page_index)

    def _load_all_pages(self) -> None:
        """Load current settings from controller into settings pages only."""
        for page in self.settings_pages:
            page.load_from_controller()

    def _save_all_pages(self) -> bool:
        """
        Save all settings pages to controller.
        Documentation pages don't have settings to save.

        Returns:
            True if successful, False if validation failed
        """
        try:
            for page in self.settings_pages:
                page.save_to_controller()
            return True

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Invalid Setting",
                f"Could not save settings:\n\n{str(e)}\n\n"
                "Please correct the value and try again."
            )
            return False

    def _on_apply(self) -> None:
        """Save settings but keep dialog open with confirmation."""
        if self._save_all_pages():
            QMessageBox.information(
                self,
                "Settings Applied",
                "Your settings have been saved and applied.\n\n"
                "Changes take effect immediately for new operations."
            )

    def _on_ok(self) -> None:
        """Save settings and close dialog with Accepted."""
        if self._save_all_pages():
            self.accept()

    def _on_restore_defaults(self) -> None:
        """
        Confirm and reset all settings to defaults.
        Only affects settings pages, not documentation.
        """
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Reset all settings to default values?\n\n"
            "This will restore:\n"
            "• Performance settings\n"
            "• Preview settings\n"
            "• Default conversion settings",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.controller.reset_to_defaults()
            self._load_all_pages()

            QMessageBox.information(
                self,
                "Defaults Restored",
                "All settings have been reset to default values."
            )
