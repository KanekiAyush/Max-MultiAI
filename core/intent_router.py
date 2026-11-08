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
        
    if "silent mode off" in text_lower or "unmute" in text_lower or "bolna shuru" in text_lower:
        tts.toggle_silent(False)
        return "Silent mode off."
    if "silent mode on" in text_lower or "mute" in text_lower:
        tts.toggle_silent(True)
        return "Theek hai Ayuu, silent mode on."

    # 🎬 MODES (Movie, Anime, Game)
    if "game mode" in text_lower or "gaming mode" in text_lower:
        return system.gaming_mode()
    if "movie mode" in text_lower:
        return system.movie_mode()
    if "anime mode" in text_lower:
        return system.anime_mode()

    # 🕵️ SECRET MODE (Incognito)
    if "secret mode" in text_lower or "incognito" in text_lower:
        # "secret mode open google.com" -> "google.com"
        query = re.sub(r'(secret mode|incognito mode|open|search|on|in|me)', '', text_lower).strip()
        return browser.open_incognito(query)

    # 🔍 SEARCH & PLAY (Startswith logic for speed)
    if text_lower.startswith("search ") or text_lower.startswith("google "):
        query = re.sub(r'^(search|google)\s+', '', text_lower).strip()
        return browser.search_google(query)
        
    if text_lower.startswith("play "):
        query = re.sub(r'^play\s+', '', text_lower).strip()
        return browser.play_on_youtube(query)

    # Baaki system commands
    if "lock" in text_lower and ("pc" in text_lower or "screen" in text_lower):
        return system.lock_pc()
    if "screenshot" in text_lower:
        return system.take_screenshot()
    if "read this" in text_lower or "padho isko" in text_lower:
        return system.read_selected_text()
    
    # Weather
    if "weather" in text_lower or "mausam" in text_lower:
        city = "Mumbai" 
        if " in " in text_lower:
            city = text_lower.split(" in ")[-1].strip()
        return system.get_weather(city)
        
    # Daily Briefing
    if "daily briefing" in text_lower:
        return system.get_daily_briefing()
        
    # File Creation
        # File Creation (Super Robust)
    if ("create" in text_lower or "make" in text_lower or "write" in text_lower) and "file" in text_lower:
        try:
            # 1. File ka naam nikalo (jo 'file' ke baad aata hai)
            file_match = re.search(r'file\s+([^\s]+)', text_lower)
            if file_match:
                filename = file_match.group(1)
                filename = re.sub(r'[^\w\.\-]', '', filename) # Clean filename
                
                # 2. Content nikalo (write, with, containing, and write ke baad ka text)
                content = ""
                content_match = re.search(r'(?:write|with|containing|and write|me)\s+(.+)', text_lower)
                if content_match:
                    content = content_match.group(1)
                    # Faltu words hatao jaise "in it", "content"
                    content = re.sub(r'\s+in\s+(it|this file|the file)$', '', content, flags=re.IGNORECASE)
                    content = content.replace("content ", "").strip()
                
                if not content:
                    content = "Empty file" # Agar sirf file banani ho
                    
                return system.write_file(filename, content)
            else:
                return "Batao file ka naam kya rakhna hai?"
        except Exception as e:
            return f"File command samajh nahi aayi: {e}"
            
    # File Deletion
        # File Deletion (Super Robust)
    if ("delete" in text_lower or "remove" in text_lower or "erase" in text_lower) and "file" in text_lower:
        try:
            # Regex: "delete file test.txt" ya "remove a file notes.txt"
            file_match = re.search(r'file\s+([^\s]+)', text_lower)
            
            # Agar user ne "file" word nahi bola, jaise "delete test.txt"
            if not file_match:
                file_match = re.search(r'(?:delete|remove|erase)\s+(?:a\s+|the\s+)?([^\s]+)', text_lower)
                
            if file_match:
                filename = file_match.group(1)
                filename = re.sub(r'[^\w\.\-]', '', filename) # Clean filename (sirf letters, numbers, dot, dash)
                return system.delete_file(filename)
            else:
                return "Kaunsi file delete karni hai? Naam batao Ayuu."
        except Exception as e:
            return f"Delete command samajh nahi aayi: {e}"
    
    # Volume & Brightness & Timer
    vol_match = re.search(r'volume\s*(\d+)', text_lower)
    if vol_match:
        return system.set_volume("up") if int(vol_match.group(1)) > 50 else system.set_volume("down")
    bright_match = re.search(r'brightness\s*(\d+)', text_lower)
    if bright_match:
        return system.set_brightness(int(bright_match.group(1)))
    timer_match = re.search(r'timer\s*(\d+)', text_lower)
    if timer_match:
        return system.set_timer(int(timer_match.group(1)), tts.speak)

    # Open App
    open_match = re.search(r'open\s+(.+)', text_lower)
    if open_match:
        app_name = open_match.group(1).replace("karo", "").strip()
        return system.open_app(app_name)
        
    # Open YouTube (Generic)
    if "open youtube" in text_lower:
        return browser.play_on_youtube("")

    # 🧠 FALLBACK TO LLM (Agar upar ka kuch bhi match nahi hua)
    log.info("Routing to LLM with context...")
    history = get_recent_history(limit=3)
    context = ""
    if history:
        context = "Pichhli baatein:\n"
        for user_msg, max_msg in history:
            context += f"User: {user_msg}\nMAX: {max_msg}\n"
            
    full_prompt = f"{context}\nUser ka naya sawaal: {text}\nMAX ka jawab:"
    reply = llm.get_response(full_prompt, use_cache=True)
    save_conversation(text, reply)
    return reply