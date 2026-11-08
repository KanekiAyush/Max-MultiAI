"""Text-to-Speech engine for MAX (Optimized for Speed)."""
import os
import asyncio
import socket
import threading
import edge_tts
import pygame
import io

from utils.logger import get_logger

log = get_logger("MAX.TTS")

class TTSManager:
    def __init__(self):
        self.is_speaking = False
        self.stop_event = threading.Event()
        self.voice = "en-IN-NeerjaNeural"
        
        # Pre-cache wale audio ke liye variables
        self.cached_haan_ayuu = None
        self.cached_haan_master = None
        
        # Start hote hi cache download kar lo
        threading.Thread(target=self._pre_cache_audio, daemon=True).start()

    def _has_internet(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5)
            return True
        except OSError:
            return False

    def _pre_cache_audio(self):
        """Pehle se audio generate karke rakh lo taaki wake word pe 0 delay ho."""
        if not self._has_internet(): return
        try:
            self.cached_haan_ayuu = self._generate_audio("Haan Ayuu?")
            self.cached_haan_master = self._generate_audio("Haan Master?")
            log.info("⚡ Cached audio ready!")
        except Exception as e:
            log.error(f"Cache generation failed: {e}")

    def _generate_audio(self, text: str) -> bytes:
        async def _generate():
            communicate = edge_tts.Communicate(text, self.voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data
        return asyncio.run(_generate())

    def speak(self, text: str) -> None:
        if not text: return
        if getattr(self, 'is_silent', False):
            log.info(f"[Silent Mode] MAX: {text}")
            return
        self.stop() # Purana audio kill karo

        def _run():
            self.is_speaking = True
            self.stop_event.clear()
            
            audio_bytes = None
            
            # Agar "Haan Ayuu" ya "Haan Master" bola hai, toh cache use karo
            if text == "Haan Ayuu?" and self.cached_haan_ayuu:
                audio_bytes = self.cached_haan_ayuu
            elif text == "Haan Master?" and self.cached_haan_master:
                audio_bytes = self.cached_haan_master
            elif self._has_internet():
                try:
                    audio_bytes = self._generate_audio(text)
                except Exception as e:
                    log.error(f"Edge TTS error: {e}")
            
            # Agar audio mil gaya (online ya cache), toh play karo
            if audio_bytes and not self.stop_event.is_set():
                try:
                    pygame.mixer.init()
                    pygame.mixer.music.load(io.BytesIO(audio_bytes))
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                        pygame.time.Clock().tick(20)
                        
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                except Exception as e:
                    log.error(f"Audio playback error: {e}")
            elif not audio_bytes:
                # Offline fallback (Windows built-in voice)
                import pyttsx3
                try:
                    engine = pyttsx3.init()
                    engine.say(text)
                    engine.runAndWait()
                except: pass
                
            self.is_speaking = False

        threading.Thread(target=_run, daemon=True).start()

    def toggle_silent(self, silent: bool) -> None:
        """Turn silent mode on or off."""
        self.is_silent = silent
        if silent:
            self.stop() # Agar bol rahi hai toh turant chup ho jaye
        log.info(f"Silent mode set to: {silent}")
    def stop(self) -> None:
        """Force stop speaking."""
        self.stop_event.set()
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except: pass

# 👇 YEH LINE MISSING THI 👇
tts = TTSManager()