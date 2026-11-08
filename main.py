"""MAX - Master Ayush's Personal AI Assistant. Main entry point."""
import sys
import json
import os
import random
import threading
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from utils.logger import get_logger
from core.tts import tts
from core.stt import STTEngine
from core.wake_word import WakeWordListener
from core.intent_router import process_input
from memory.database import init_db

log = get_logger("MAX.main")

ROOT = Path(__file__).parent
CONFIG_DIR = ROOT / "config"
LOGS_DIR = ROOT / "logs"
DATA_DIR = ROOT / "data"


def ensure_folders() -> None:
    for folder in [CONFIG_DIR, LOGS_DIR, DATA_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
    log.info("Folders verified: logs/, data/, config/")


def run_gui() -> int:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from gui.main_window import MainWindow
    from gui.tray import SystemTrayIcon

    app = QApplication(sys.argv)
    app.setApplicationName("MAX")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    tray = SystemTrayIcon()

    def restore_window() -> None:
        if getattr(window, '_was_maximized', False):
            window.showMaximized()
        else:
            window.showNormal()
        window.raise_()
        window.activateWindow()
        window.setUpdatesEnabled(False)
        window.setUpdatesEnabled(True)
        window.repaint()

    tray.show_window.connect(restore_window)
    tray.quit_app.connect(app.quit)

    with open(CONFIG_DIR / "wake_words.json", "r") as f:
        ww_config = json.load(f)
        
    vosk_model_path = ROOT / ww_config["vosk_model_path"]
    
    stt = STTEngine(model_path=vosk_model_path)
    wake_word_listener = WakeWordListener(
        model_path=vosk_model_path,
        wake_words=ww_config["wake_words"]
    )

    def process_voice_input():
        window.set_state("listening")
        wake_word_listener.pause()
        
        def _listen_thread():
            # time.sleep hata diya
            def _on_processing():
                wake_word_listener.stt_processing.emit()
                
            text = stt.listen(timeout=8, on_processing=_on_processing)
            wake_word_listener.stt_finished.emit(text)
            
        threading.Thread(target=_listen_thread, daemon=True).start()

    def on_stt_finished(text: str):
        if not text or len(text.strip()) < 2:
            log.info("No valid speech detected.")
            on_speech_done()
            return
        handle_text(text)

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
                
            # Safely emit to main GUI thread
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

    def check_tts_and_listen():
        if tts.is_speaking:
            # Har 50ms me check karega
            QTimer.singleShot(50, check_tts_and_listen)
        else:
            log.info("TTS finished. Listening instantly...")
            # 50ms ka chhota sa gap taaki audio buffer clear ho jaye
            QTimer.singleShot(50, process_voice_input)

    def on_wake_word_detected():
        log.info("Wake word detected. Activating MAX.")
        tts.stop() 
        window.set_state("speaking")
        
        addr = random.choice(["Ayuu", "Master"])
        tts.speak(f"Haan {addr}?")
        
        check_tts_and_listen()

    # --- SIGNAL CONNECTIONS ---
    window.text_submitted.connect(handle_text)
    window.mic_pressed.connect(handle_mic)
    window.stop_pressed.connect(handle_stop)
    window.reply_ready_signal.connect(_update_ui_with_reply)  # <-- YEH MISSING THA
    
    wake_word_listener.wake_word_detected.connect(on_wake_word_detected)
    wake_word_listener.stt_finished.connect(on_stt_finished)
    wake_word_listener.stt_processing.connect(lambda: window.set_state("thinking"))

    # --- Battery Monitor ---
    def start_battery_monitor():
        import psutil, time
        warned = False
        while True:
            try:
                battery = psutil.sensors_battery()
                if battery and battery.percent <= 20 and not battery.power_plugged and not warned:
                    msg = "Ayuu, battery 20% se neeche aa gayi hai! Please charger laga do."
                    QTimer.singleShot(0, lambda: window.append_chat("MAX", msg))
                    QTimer.singleShot(0, lambda: tts.speak(msg))
                    warned = True
                elif battery and battery.power_plugged:
                    warned = False
            except Exception as e:
                log.error(f"Battery check failed: {e}")
            time.sleep(60)

    threading.Thread(target=start_battery_monitor, daemon=True).start()
    wake_word_listener.start()

    window.show()
    log.info("GUI launched. MAX is fully awake.")
    return app.exec()


def start_max() -> None:
    log.info("=" * 50)
    log.info("MAX is starting...")
    log.info("=" * 50)
    ensure_folders()
    init_db()
    log.info("✨ Launching GUI...")
    run_gui()


def main() -> int:
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