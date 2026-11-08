"""Routes user input to LLM or System Skills."""
import re
from ai.llm_client import llm
from skills import system, browser

from memory.database import save_conversation, get_recent_history
from core.tts import tts
from utils.logger import get_logger

log = get_logger("MAX.Router")

def process_input(text: str) -> str:
    text_lower = text.lower().strip()
    
    # 🛑 STOP & MUTE COMMANDS
    if re.search(r'\b(stop|ruk|chup|band karo)\b', text_lower):
        tts.stop() 
        return ""
    if "silent mode" in text_lower or "mute" in text_lower:
        tts.toggle_silent(True)
        return "Theek hai Ayuu, silent mode on."
    if "unmute" in text_lower:
        tts.toggle_silent(False)
        return "Silent mode off."

    # 🎯 SMART REGEX ROUTER (0 Tokens, Instant)
    # 1. System Commands
    if "lock" in text_lower and ("pc" in text_lower or "screen" in text_lower):
        return system.lock_pc()
    if "game mode" in text_lower or "gaming mode" in text_lower:
        return system.gaming_mode()
    if "screenshot" in text_lower:
        return system.take_screenshot()
    if "read this" in text_lower or "padho isko" in text_lower:
        return system.read_selected_text()
    
    # Volume (jaise "volume 50" ya "increase volume")
    vol_match = re.search(r'volume\s*(\d+)', text_lower)
    if vol_match:
        # Yahan humne system.set_volume me percentage logic add karna padega, abhi ke liye up/down use kar rahe hain
        return system.set_volume("up") if int(vol_match.group(1)) > 50 else system.set_volume("down")
    
    # Brightness
    bright_match = re.search(r'brightness\s*(\d+)', text_lower)
    if bright_match:
        return system.set_brightness(int(bright_match.group(1)))

    # Timer
    timer_match = re.search(r'timer\s*(\d+)', text_lower)
    if timer_match:
        return system.set_timer(int(timer_match.group(1)), tts.speak)

    # 2. Browser Commands
    if "open youtube" in text_lower or "play" in text_lower:
        query = re.sub(r'(open youtube|play|on youtube)', '', text_lower).strip()
        return browser.play_on_youtube(query)
    if "search" in text_lower:
        query = re.sub(r'(search|google)', '', text_lower).strip()
        return browser.search_google(query)
    
    # Open App (Generic)
    open_match = re.search(r'open\s+(.+)', text_lower)
    if open_match:
        app_name = open_match.group(1).replace("karo", "").strip()
        return system.open_app(app_name)

    # 🧠 FALLBACK TO LLM (Sirf complex sawaalon ke liye)
    log.info("Routing to LLM with context...")
    history = get_recent_history(limit=3)
    context = ""
    if history:
        context = "Pichhli baatein:\n"
        for user_msg, max_msg in history:
            context += f"User: {user_msg}\nMAX: {max_msg}\n"
            
    full_prompt = f"{context}\nUser ka naya sawaal: {text}\nMAX ka jawab:"
    
    # Yahan hum use_cache=True rakh rahe hain
    reply = llm.get_response(full_prompt, use_cache=True)
    save_conversation(text, reply)
    return reply