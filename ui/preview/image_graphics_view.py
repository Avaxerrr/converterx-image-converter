"""
Custom QGraphicsView with zoom capabilities.
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent, QPainter


class ImageGraphicsView(QGraphicsView):
    """Custom QGraphicsView with zoom capabilities."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

        # View settings
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()

        if delta > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15

        new_zoom = self.zoom_factor * factor

        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.zoom_factor = new_zoom
