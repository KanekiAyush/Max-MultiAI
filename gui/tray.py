"""System tray icon for MAX - runs in background when window is hidden."""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QObject, Signal


class SystemTrayIcon(QObject):
    """Tray icon with Show/Quit menu."""

    show_window = Signal()
    quit_app = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tray = QSystemTrayIcon(self._make_icon())
        self.tray.setToolTip("MAX — Personal AI Assistant")

        menu = QMenu()
        show_action = menu.addAction("Show MAX")
        show_action.triggered.connect(self.show_window.emit)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app.emit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _make_icon(self) -> QIcon:
        """Draw a small arc-reactor-style icon programmatically."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor(0, 180, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(6, 6, 52, 52)

        painter.setBrush(QColor(10, 14, 39))
        painter.drawEllipse(16, 16, 32, 32)

        painter.setBrush(QColor(0, 212, 255))
        painter.drawEllipse(24, 24, 16, 16)

        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(28, 28, 8, 8)

        painter.end()
        return QIcon(pixmap)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window.emit()

    def show_message(self, title: str, message: str) -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.Information, 3000)