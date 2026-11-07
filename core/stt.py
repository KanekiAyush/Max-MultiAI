"""Speech-to-Text engine using SpeechRecognition (Google) with Vosk fallback."""
import speech_recognition as sr
import json
import vosk
import sounddevice as sd
import numpy as np
from utils.logger import get_logger

log = get_logger("MAX.STT")

class STTEngine:
    def __init__(self, model_path="models/vosk-model-small-en-us-0.15"):
        log.info("Initializing STT Engine (Primary: Google API, Fallback: Vosk)...")
        
        # 1. Google Recognizer Setup
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0 # 1 second silence pe rukega
        
        # 2. Vosk Fallback Setup (agar internet na ho)
        try:
            self.vosk_model = vosk.Model(str(model_path))
            self.vosk_rec = vosk.KaldiRecognizer(self.vosk_model, 16000)
        except Exception as e:
            log.warning(f"Vosk fallback could not load: {e}")
            self.vosk_model = None

    def listen(self, timeout=5, on_processing=None) -> str:
        log.info("🎤 Listening...")
        
        # Primary: Google Speech Recognition
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    log.info("Timeout: Koi aawaz nahi aayi.")
                    return ""
            
            if on_processing:
                on_processing()
                
            log.info("🧠 Transcribing with Google...")
            text = self.recognizer.recognize_google(audio, language="en-IN").lower()
            log.info(f"📝 Transcribed (Google): '{text}'")
            return text
            
        except sr.UnknownValueError:
            log.info("Google could not understand the audio.")
            return ""
        except sr.RequestError as e:
            log.warning(f"Google API failed ({e}), switching to Vosk...")
            # Fallback to Vosk (offline)
            if self.vosk_model:
                return self._listen_vosk(on_processing)
            return ""
        except Exception as e:
            log.error(f"STT Error: {e}")
            return ""

    def _listen_vosk(self, on_processing) -> str:
        """Offline fallback using Vosk."""
        log.info("🎤 Listening (Vosk Fallback)...")
        audio_data = []
        
        def callback(indata, frames, time_info, status):
            audio_data.append(bytes(indata))
            
        try:
            # 5 seconds record karega
            with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
                sd.sleep(5000) 
                
            if on_processing:
                on_processing()
                
            log.info("🧠 Transcribing with Vosk...")
            for chunk in audio_data:
                self.vosk_rec.AcceptWaveform(chunk)
            result = json.loads(self.vosk_rec.FinalResult())
            text = result.get("text", "").strip().lower()
            log.info(f"📝 Transcribed (Vosk): '{text}'")
            return text
        except Exception as e:
            log.error(f"Vosk Error: {e}")
            return ""

    def stop_listening(self):
        pass