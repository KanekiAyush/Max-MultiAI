"""Text-to-Speech engine for MAX."""
import os
import asyncio
import socket
import threading
import edge_tts
import pyttsx3
import pygame
import multiprocessing
import io

from utils.logger import get_logger

log = get_logger("MAX.TTS")

def _play_audio_process(audio_bytes):
    """Ye function alag process me chalega."""
    try:
        pygame.mixer.init()
        # File save karne ki zaroorat nahi, direct memory se play karo
        pygame.mixer.music.load(io.BytesIO(audio_bytes))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        pass
    finally:
        pygame.mixer.quit()

def _offline_tts_process(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except:
        pass

class TTSManager:
    def __init__(self):
        self.is_speaking = False
        self.current_process = None

    def _has_internet(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5)
            return True
        except OSError:
            return False

    def speak(self, text: str) -> None:
        if not text:
            return

        self.stop() # Pehle purana kill karo

        def _run():
            self.is_speaking = True
            
            if self._has_internet():
                try:
                    voice = "en-IN-NeerjaNeural"
                    async def _generate():
                        communicate = edge_tts.Communicate(text, voice)
                        audio_data = b""
                        async for chunk in communicate.stream():
                            if chunk["type"] == "audio":
                                audio_data += chunk["data"]
                        return audio_data
                    
                    audio_bytes = asyncio.run(_generate())
                    
                    if audio_bytes:
                        # Alag process start karo audio play karne ke liye
                        self.current_process = multiprocessing.Process(target=_play_audio_process, args=(audio_bytes,))
                        self.current_process.start()
                        self.current_process.join()
                except Exception as e:
                    log.error(f"Edge TTS error: {e}")
                    # Fallback to offline
                    self.current_process = multiprocessing.Process(target=_offline_tts_process, args=(text,))
                    self.current_process.start()
                    self.current_process.join()
            else:
                self.current_process = multiprocessing.Process(target=_offline_tts_process, args=(text,))
                self.current_process.start()
                self.current_process.join()
                
            self.is_speaking = False

        threading.Thread(target=_run, daemon=True).start()

    def stop(self) -> None:
        """Force kill the TTS process."""
        if self.current_process and self.current_process.is_alive():
            self.current_process.terminate() # Process ko zabardasti maaro
            self.current_process.join()
            self.current_process = None
            log.info("TTS forcefully stopped.")
        
tts = TTSManager()