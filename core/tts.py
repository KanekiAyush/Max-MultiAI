"""Text-to-Speech engine for MAX (Optimized & Crash-Proof)."""
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
        # Ek hi baar initialize karo
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        self.is_speaking = False
        self.stop_event = threading.Event()
        self.voice = "en-IN-NeerjaNeural"
        self.is_silent = False  # 👈 YEH MISSING THA
        
        self.cached_haan_ayuu = None
        self.cached_haan_master = None
        
        threading.Thread(target=self._pre_cache_audio, daemon=True).start()

    def toggle_silent(self, silent: bool) -> None:
        self.is_silent = silent
        if silent:
            self.stop()
        log.info(f"Silent mode set to: {silent}")

    def _has_internet(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5)
            return True
        except OSError:
            return False

    def _pre_cache_audio(self):
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
        
        # 👇 SILENT MODE CHECK 👇
        if self.is_silent:
            log.info(f"[Silent Mode] MAX: {text}")
            return
            
        self.stop() # Purana audio kill karo

        self.is_speaking = True
        self.stop_event.clear()

        def _run():
            audio_bytes = None
            
            if text == "Haan Ayuu?" and self.cached_haan_ayuu:
                audio_bytes = self.cached_haan_ayuu
            elif text == "Haan Master?" and self.cached_haan_master:
                audio_bytes = self.cached_haan_master
            elif self._has_internet():
                try:
                    audio_bytes = self._generate_audio(text)
                except Exception as e:
                    log.error(f"Edge TTS error: {e}")
            
            if audio_bytes and not self.stop_event.is_set():
                try:
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                        
                    pygame.mixer.music.load(io.BytesIO(audio_bytes))
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                        pygame.time.Clock().tick(20)
                        
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                except Exception as e:
                    log.error(f"Audio playback error: {e}")
            elif not audio_bytes:
                import pyttsx3
                try:
                    engine = pyttsx3.init()
                    engine.say(text)
                    engine.runAndWait()
                except: pass
                
            self.is_speaking = False

        threading.Thread(target=_run, daemon=True).start()

    def stop(self) -> None:
        self.stop_event.set()
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except: 
            pass

tts = TTSManager()