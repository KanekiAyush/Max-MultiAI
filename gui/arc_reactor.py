"""Rotating arc reactor animation widget - the visual heart of MAX."""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient


class ArcReactorWidget(QWidget):
    """Animated arc reactor that rotates and pulses based on AI state."""

    # State -> (color, speed_multiplier)
    STATE_COLORS = {
        "idle": QColor(0, 180, 255),
        "listening": QColor(0, 255, 120),
        "thinking": QColor(180, 100, 255),
        "speaking": QColor(255, 180, 0),
    }
    STATE_SPEEDS = {
        "idle": 1.0,
        "listening": 2.2,
        "thinking": 3.2,
        "speaking": 1.6,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 260)
        self.state = "idle"
        self.angle_outer = 0.0
        self.angle_middle = 0.0
        self.angle_inner = 0.0
        self.pulse = 0.0
        self.pulse_dir = 1

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)  # ~60 FPS

    def set_state(self, state: str) -> None:
        """Change animation state: idle / listening / thinking / speaking."""
        if state not in self.STATE_COLORS:
            state = "idle"
        self.state = state
        self.update()

    def _animate(self) -> None:
        speed = self.STATE_SPEEDS.get(self.state, 1.0)
        self.angle_outer = (self.angle_outer + 2.0 * speed) % 360
        self.angle_middle = (self.angle_middle - 3.0 * speed) % 360
        self.angle_inner = (self.angle_inner + 4.5 * speed) % 360

        self.pulse += 0.03 * self.pulse_dir * speed
        if self.pulse >= 1.0:
            self.pulse = 1.0
            self.pulse_dir = -1
        elif self.pulse <= 0.0:
            self.pulse = 0.0
            self.pulse_dir = 1

        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = self.width() / 2.0, self.height() / 2.0
        base_r = min(self.width(), self.height()) / 2.0 - 20
        color = self.STATE_COLORS.get(self.state, QColor(0, 180, 255))

        # Outer glow
        grad = QRadialGradient(cx, cy, base_r)
        c1 = QColor(color); c1.setAlpha(90)
        c2 = QColor(color); c2.setAlpha(0)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), base_r, base_r)

        # Outer dashed ring
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_outer)
        painter.setPen(QPen(color, 4))
        painter.setBrush(Qt.NoBrush)
        r = base_r * 0.95
        for i in range(0, 360, 45):
            painter.drawArc(int(-r), int(-r), int(r * 2), int(r * 2), i * 16, 30 * 16)
        painter.restore()

        # Middle ring
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_middle)
        painter.setPen(QPen(color.lighter(120), 3))
        painter.setBrush(Qt.NoBrush)
        r = base_r * 0.72
        for i in range(0, 360, 60):
            painter.drawArc(int(-r), int(-r), int(r * 2), int(r * 2), i * 16, 40 * 16)
        painter.restore()

        # Inner ring
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_inner)
        painter.setPen(QPen(color.lighter(140), 2))
        painter.setBrush(Qt.NoBrush)
        r = base_r * 0.52
        painter.drawEllipse(QPointF(0, 0), r, r)
        painter.restore()

        # Center pulsing core
        core_r = base_r * 0.35 * (1.0 + self.pulse * 0.12)
        core_grad = QRadialGradient(cx, cy, core_r)
        inner = QColor(255, 255, 255, 220)
        mid = color.lighter(130)
        mid.setAlpha(220)
        edge = QColor(color); edge.setAlpha(90)
        core_grad.setColorAt(0, inner)
        core_grad.setColorAt(0.55, mid)
        core_grad.setColorAt(1, edge)
        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(color, 2))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)