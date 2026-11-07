"""Routes user input to LLM or System Skills."""
import re
from ai.llm_client import llm
from skills import system, browser
from memory.database import save_conversation, get_recent_history
from core.tts import tts
from utils.logger import get_logger

log = get_logger("MAX.Router")

def process_input(text: str) -> str:
    text_lower = text.lower()
    if "stop" in text_lower or "chup" in text_lower or "band karo" in text_lower:
        tts.stop() # Bolna band karo
        return ""  # Khaali return karo taaki naya reply na aaye
    reply = ""
    
    # 1. System Commands
    if "lock" in text_lower and ("pc" in text_lower or "screen" in text_lower):
        reply = system.lock_pc()
    elif "game mode" in text_lower or "gaming mode" in text_lower:
        reply = system.gaming_mode()
    elif "screenshot" in text_lower:
        reply = system.take_screenshot()
    elif "read this" in text_lower or "read selected" in text_lower or "padho isko" in text_lower:
        reply = system.read_selected_text()
    elif "read screen" in text_lower or "screen pe kya hai" in text_lower:
        reply = system.read_screen()
    elif "volume" in text_lower:
        reply = system.set_volume(text_lower)
    elif "brightness" in text_lower:
        # Simple extraction: "brightness 50" -> 50
        match = re.search(r'\d+', text_lower)
        level = int(match.group()) if match else 100
        reply = system.set_brightness(level)
    elif "timer" in text_lower or "alarm" in text_lower:
        # Simple extraction: "timer 10 seconds" -> 10
        match = re.search(r'\d+', text_lower)
        seconds = int(match.group()) if match else 5
        reply = system.set_timer(seconds, tts.speak)
        
    # 2. Browser Commands
    elif "open youtube" in text_lower or "play" in text_lower:
        query = text_lower.replace("open youtube", "").replace("play", "").strip()
        reply = browser.play_on_youtube(query)
    elif "search" in text_lower:
        query = text_lower.replace("search", "").replace("google", "").strip()
        reply = browser.search_google(query)
    elif "open" in text_lower:
        app_name = text_lower.replace("open", "").replace("karo", "").strip()
        reply = system.open_app(app_name)
        
    # 3. Fallback to LLM (with Memory context)
    if not reply:
        log.info("Routing to LLM with context...")
        # Pichhli 3 baatein uthao
        history = get_recent_history(limit=3)
        context = ""
        if history:
            context = "Pichhli baatein:\n"
            for user_msg, max_msg in history:
                context += f"User: {user_msg}\nMAX: {max_msg}\n"
                
        full_prompt = f"{context}\nUser ka naya sawaal: {text}\nMAX ka jawab:"
        reply = llm.get_response(full_prompt)
        
    # Save to memory
    save_conversation(text, reply)
    return reply