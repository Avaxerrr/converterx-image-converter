"""
Collapsible section widget for accordion-style UI.

This widget provides an expandable/collapsible section with a toggle button
and customizable content area. Used throughout the settings panel.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QSizePolicy
from PySide6.QtCore import Qt


class CollapsibleSection(QWidget):
    """A collapsible section widget (accordion-style) with customizable spacing."""

    def __init__(self, title: str, content_spacing: int = 6, parent=None):
        super().__init__(parent)

        # Toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setProperty("class", "collapsible-header")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.clicked.connect(self._on_toggle)
        self.toggle_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Content area
        self.content_area = QWidget()
        self.content_area.setProperty("class", "collapsible-content")
        self.content_layout = QVBoxLayout(self.content_area)

        # ✅ CUSTOM SPACING per section
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(content_spacing)  # Use parameter

        self.content_area.hide()

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def _on_toggle(self):
        """Toggle content visibility."""
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.content_area.setVisible(checked)

    def set_content_layout(self, layout):
        """Set the layout for the collapsible content."""
        # Clear existing
        while self.content_layout.count():
            self.content_layout.takeAt(0)

        # Add new content
        if isinstance(layout, (QVBoxLayout, QHBoxLayout)):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    self.content_layout.addWidget(item.widget())
                elif item.layout():
                    self.content_layout.addLayout(item.layout())
        else:
            self.content_layout.addLayout(layout)