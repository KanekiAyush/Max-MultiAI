"""Main application window for MAX."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from gui.arc_reactor import ArcReactorWidget


class MainWindow(QMainWindow):
    """Main MAX window with arc reactor, chat, and controls."""

    text_submitted = Signal(str)
    mic_pressed = Signal()
    stop_pressed = Signal()

    STATE_LABELS = {
        "idle": "💤  Idle",
        "listening": "🎤  Listening...",
        "thinking": "💭  Thinking...",
        "speaking": "🔊  Speaking...",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAX — Master Ayush's Personal AI Assistant")
        self.setMinimumSize(720, 820)
        self.setStyleSheet(self._stylesheet())
        self._build_ui()
        self._was_maximized = False
        self._setup_shortcuts()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Header
        title = QLabel("M A X")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 26, QFont.Bold))
        root.addWidget(title)

        subtitle = QLabel("Master Ayush's Personal AI Assistant")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        # Arc reactor
        self.reactor = ArcReactorWidget()
        root.addWidget(self.reactor, stretch=3)

        # Status
        self.status_label = QLabel(self.STATE_LABELS["idle"])
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("status")
        self.status_label.setFont(QFont("Segoe UI", 13))
        root.addWidget(self.status_label)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setObjectName("chat")
        self.chat_display.setMinimumHeight(160)
        root.addWidget(self.chat_display, stretch=2)

        # Text input row
        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command or press Mic...")
        self.input_field.setObjectName("input")
        self.input_field.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_field, stretch=5)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendbtn")
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.send_btn, stretch=1)
        root.addLayout(input_row)

        # Bottom buttons
        bottom = QHBoxLayout()
        self.mic_btn = QPushButton("🎤  Mic")
        self.mic_btn.setObjectName("micbtn")
        self.mic_btn.clicked.connect(self.mic_pressed.emit)
        bottom.addWidget(self.mic_btn)

        self.stop_btn = QPushButton("⏹  STOP  (F9)")
        self.stop_btn.setObjectName("stopbtn")
        self.stop_btn.clicked.connect(self.stop_pressed.emit)
        bottom.addWidget(self.stop_btn)

        self.tray_btn = QPushButton("📥  Tray")
        self.tray_btn.setObjectName("traybtn")
        self.tray_btn.clicked.connect(self.minimize_to_tray)
        
        bottom.addWidget(self.tray_btn)

        root.addLayout(bottom)
    

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("F9"), self, activated=self.stop_pressed.emit)

    def minimize_to_tray(self) -> None:
            """Save state before hiding to prevent white screen bug."""
            self._was_maximized = self.isMaximized()
            self.hide()
    
    def _on_send(self) -> None:
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.text_submitted.emit(text)

    def set_state(self, state: str, custom_text: str = None) -> None:
        """Update reactor + status label."""
        self.reactor.set_state(state)
        self.status_label.setText(custom_text or self.STATE_LABELS.get(state, "💤  Idle"))

    def append_chat(self, speaker: str, text: str) -> None:
        """Add message to the chat display."""
        color = "#00d4ff" if speaker.upper() == "MAX" else "#ffffff"
        label = "MAX" if speaker.upper() == "MAX" else "You"
        safe_text = (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
        self.chat_display.append(
            f'<span style="color:{color};"><b>{label}:</b></span> {safe_text}'
        )

    def _stylesheet(self) -> str:
        return """
        QMainWindow, QWidget {
            background-color: #0a0e27;
        }
        QLabel#title {
            color: #00d4ff;
            letter-spacing: 6px;
        }
        QLabel#subtitle {
            color: #6b7a99;
            font-size: 11pt;
        }
        QLabel#status {
            color: #00d4ff;
            padding: 6px;
        }
        QTextEdit#chat {
            background-color: #0f1535;
            color: #e0e0e0;
            border: 1px solid #1e2a5a;
            border-radius: 10px;
            padding: 10px;
            font-size: 11pt;
        }
        QLineEdit#input {
            background-color: #0f1535;
            color: #ffffff;
            border: 1px solid #1e2a5a;
            border-radius: 10px;
            padding: 10px;
            font-size: 11pt;
        }
        QLineEdit#input:focus {
            border: 1px solid #00d4ff;
        }
        QPushButton {
            background-color: #1e2a5a;
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 10px 16px;
            font-size: 11pt;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2e3a7a;
        }
        QPushButton#sendbtn {
            background-color: #00b4ff;
            color: #0a0e27;
        }
        QPushButton#sendbtn:hover {
            background-color: #00d4ff;
        }
        QPushButton#stopbtn {
            background-color: #8b1e1e;
        }
        QPushButton#stopbtn:hover {
            background-color: #c03636;
        }
        """