"""MAX - Master Ayush's Personal AI Assistant. Main entry point."""
import sys
import json
import os
import random
import threading
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from utils.logger import get_logger
from core.tts import tts
from core.stt import STTEngine
from core.wake_word import WakeWordListener
from core.intent_router import process_input
from memory.database import init_db

log = get_logger("MAX.main")

# Project paths
ROOT = Path(__file__).parent
CONFIG_DIR = ROOT / "config"
LOGS_DIR = ROOT / "logs"
DATA_DIR = ROOT / "data"


def ensure_folders() -> None:
    """Create required folders if missing."""
    for folder in [CONFIG_DIR, LOGS_DIR, DATA_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
    log.info("Folders verified: logs/, data/, config/")


def run_gui() -> int:
    """Launch the GUI application."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from gui.main_window import MainWindow
    from gui.tray import SystemTrayIcon

    app = QApplication(sys.argv)
    app.setApplicationName("MAX")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    tray = SystemTrayIcon()

    # ---- Fix for Tray Restore Bug ----
    def restore_window() -> None:
        if getattr(window, '_was_maximized', False):
            window.showMaximized()
        else:
            window.showNormal()
        
        window.raise_()
        window.activateWindow()
        
        # Force Qt to redraw
        window.setUpdatesEnabled(False)
        window.setUpdatesEnabled(True)
        window.repaint()

    # Wire tray signals
    tray.show_window.connect(restore_window)
    tray.quit_app.connect(app.quit)

    # --- Initialize Engines ---
    with open(CONFIG_DIR / "wake_words.json", "r") as f:
        ww_config = json.load(f)
        
    vosk_model_path = ROOT / ww_config["vosk_model_path"]
    
    # Initialize Vosk STT
    stt = STTEngine(model_path=vosk_model_path)
    
    # Initialize Wake Word Listener
    wake_word_listener = WakeWordListener(
        model_path=vosk_model_path,
        wake_words=ww_config["wake_words"]
    )

    # --- STT Thread Helper ---
    def process_voice_input():
        window.set_state("listening")
        wake_word_listener.pause()
        
        def _listen_thread():
            import time
            # Vosk ko mic release karne ke liye 0.8 second ka time do
            time.sleep(0.8) 
            
            def _on_processing():
                wake_word_listener.stt_processing.emit()
                
            text = stt.listen(timeout=6, on_processing=_on_processing)
            wake_word_listener.stt_finished.emit(text)
            
        threading.Thread(target=_listen_thread, daemon=True).start()

    def on_stt_finished(text: str):
        if not text or len(text.strip()) < 2:
            log.info("No valid speech detected.")
            on_speech_done()
            return
        handle_text(text)

    # --- Handlers ---
    def handle_text(text: str) -> None:
        log.info(f"User: {text}")
        window.append_chat("You", text)
        
        window.set_state("thinking")
        
        def _process_thread():
            try:
                reply = process_input(text)
            except Exception as e:
                log.error(f"Error in process_input: {e}")
                reply = "Sorry Ayuu, mujhe samajh nahi aaya ya kuch error aa gaya."
                
            # QTimer ki jagah window ke signal se update karo (Safe method)
            window.reply_ready_signal.emit(reply)
            
        threading.Thread(target=_process_thread, daemon=True).start()

    def _update_ui_with_reply(reply: str):
        if not reply:
            on_speech_done()
            return
            
        window.append_chat("MAX", reply)
        window.set_state("speaking")
        tts.speak(reply)
        
        duration = max(2000, len(reply) * 60)
        QTimer.singleShot(duration, on_speech_done)

    def _update_ui_with_reply(reply: str):
        if not reply:
            on_speech_done()
            return
            
        window.append_chat("MAX", reply)
        window.set_state("speaking")
        tts.speak(reply)
        
        duration = max(2000, len(reply) * 60)
        QTimer.singleShot(duration, on_speech_done)

    def on_speech_done():
        window.set_state("idle")
        wake_word_listener.resume()

    def handle_mic() -> None:
        log.info("Manual Mic press")
        process_voice_input()

    def handle_stop() -> None:
        log.info("STOP pressed.")
        tts.stop()
        stt.stop_listening()
        window.set_state("idle")
        wake_word_listener.resume()

    # --- Smart Wait Logic ---
    def check_tts_and_listen():
        # Jab tak MAX bol rahi hai (ya audio generate ho raha hai), wait karo
        if tts.is_speaking:
            QTimer.singleShot(100, check_tts_and_listen)
        else:
            # Jab bolna khatam ho jaye, tab exact 1.5 second ka gap do taaki echo clear ho jaye
            log.info("TTS finished. Waiting for echo to clear...")
            QTimer.singleShot(1500, process_voice_input)

    def on_wake_word_detected():
        log.info("Wake word detected. Activating MAX.")
        tts.stop() 
        window.set_state("speaking")
        
        addr = random.choice(["Ayuu", "Master"])
        tts.speak(f"Haan {addr}?")
        
        # Smart wait logic call karo
        check_tts_and_listen()

    # Connect signals
    window.text_submitted.connect(handle_text)
    window.reply_ready_signal.connect(_update_ui_with_reply)
    window.mic_pressed.connect(handle_mic)
    window.stop_pressed.connect(handle_stop)
    
    wake_word_listener.wake_word_detected.connect(on_wake_word_detected)
    wake_word_listener.stt_finished.connect(on_stt_finished)
    wake_word_listener.stt_processing.connect(lambda: window.set_state("thinking"))

    # Start wake word listener
    wake_word_listener.start()

    window.show()
    log.info("GUI launched. MAX is fully awake.")
    return app.exec()


def start_max() -> None:
    """Bootstrap MAX."""
    log.info("=" * 50)
    log.info("MAX is starting...")
    log.info("=" * 50)
    
    ensure_folders()
    init_db()  # Initialize Memory Database
    log.info("✨ Launching GUI...")
    run_gui()


def main() -> int:
    """Main entry — wrap everything to prevent crash."""
    try:
        start_max()
        return 0
    except KeyboardInterrupt:
        log.info("Stopped by user.")
        return 0
    except Exception as e:
        log.exception(f"Fatal error during startup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())