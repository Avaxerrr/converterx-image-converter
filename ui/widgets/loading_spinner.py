"""
Animated loading spinner widget.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen
import math


class LoadingSpinner(QWidget):
    """Pulsing ring spinner."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 0.0
        self.opacity = 1.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.setMinimumSize(60, 60)

    def start(self):
        self.timer.start(30)  # 33 FPS

    def stop(self):
        self.timer.stop()
        self.scale = 0.0
        self.opacity = 1.0
        self.update()

    def _animate(self):
        self.scale += 0.05
        if self.scale > 1.0:
            self.scale = 0.0
            self.opacity = 1.0
        self.opacity = 1.0 - self.scale
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        max_radius = min(self.width(), self.height()) / 2 - 5

        # Draw expanding ring
        radius = max_radius * self.scale
        color = QColor(79, 195, 247)  # #4fc3f7
        color.setAlphaF(self.opacity)

        pen = QPen(color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        painter.drawEllipse(
            int(center_x - radius),
            int(center_y - radius),
            int(radius * 2),
            int(radius * 2)
        )
