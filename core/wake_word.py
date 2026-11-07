"""Wake word listener using Vosk."""
import queue
import json
import threading
import time
import sounddevice as sd
import vosk
from PySide6.QtCore import QObject, Signal
from utils.logger import get_logger

log = get_logger("MAX.WakeWord")


class WakeWordListener(QObject):
    wake_word_detected = Signal()
    stt_finished = Signal(str)
    stt_processing = Signal() # Naya signal UI ke liye

    def __init__(self, model_path, wake_words, sample_rate=16000):
        super().__init__()
        self.model_path = str(model_path)
        self.wake_words = [w.lower() for w in wake_words]
        self.sample_rate = sample_rate
        self.q = queue.Queue()
        self.is_running = False
        self.is_paused = False
        self.stream = None

    def _callback(self, indata, frames, time_info, status):
        self.q.put(bytes(indata))

    def start(self):
        self.is_running = True
        threading.Thread(target=self._run, daemon=True).start()
        log.info("👂 Wake word listener started in background.")

    def _run(self):
        try:
            model = vosk.Model(self.model_path)
            rec = vosk.KaldiRecognizer(model, self.sample_rate)
            
            while self.is_running:
                if self.is_paused:
                    if self.stream is not None:
                        self.stream.stop()
                        self.stream.close()
                        self.stream = None
                    time.sleep(0.2)
                    continue
                    
                if self.stream is None:
                    self.q = queue.Queue()
                    self.stream = sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000, dtype='int16',
                                                    channels=1, callback=self._callback)
                    self.stream.start()
                
                try:
                    data = self.q.get(timeout=0.5)
                except queue.Empty:
                    continue
                    
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower()
                    
                    if text:
                        if any(word in text for word in self.wake_words):
                            log.info(f"🔔 Wake word detected: '{text}'")
                            self.pause() 
                            self.wake_word_detected.emit()
        except Exception as e:
            log.error(f"Wake word listener error: {e}")

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.is_running = False