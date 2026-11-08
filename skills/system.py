"""System control skills for MAX."""
import os
import subprocess
import pyautogui
import psutil
import threading
import time
from PIL import ImageGrab
from utils.logger import get_logger
import pygetwindow as gw
from PIL import ImageGrab
import pyperclip



import pytesseract
# Tesseract ka path set karo
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

log = get_logger("MAX.Skills.System")

def lock_pc() -> str:
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "PC lock kar diya hai, Ayuu."

def open_app(app_name: str) -> str:
    app_name = app_name.lower()
    try:
        if "chrome" in app_name:
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            # subprocess.Popen use kar rahe hain taaki thread block na ho
            subprocess.Popen([chrome_path, "--profile-directory=Default"])
            return "Chrome open kar rahi hoon, Ayuu."
        elif "notepad" in app_name:
            subprocess.Popen(["notepad.exe"])
            return "Notepad open ho gaya."
        elif "steam" in app_name:
            os.system("start steam://open/main")
            return "Steam open ho raha hai."
        elif "whatsapp" in app_name:
            subprocess.Popen(["cmd", "/c", "start", "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"])
            return "WhatsApp open kar rahi hoon, Master."
        else:
            os.system(f"start {app_name}")
            return f"{app_name} open karne ki koshish kar rahi hoon."
    except Exception as e:
        log.error(f"Failed to open app: {e}")
        return f"Sorry Ayuu, {app_name} open nahi kar payi."

def create_folder(path: str) -> str:
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder ban gaya: {path}"
    except Exception as e:
        return f"Folder nahi bana payi: {e}"

def take_screenshot() -> str:
    try:
        filename = "screenshot.png"
        pyautogui.screenshot(filename)
        return "Screenshot lekar 'screenshot.png' naam se save kar liya hai."
    except Exception as e:
        return f"Screenshot fail: {e}"

def gaming_mode() -> str:
    try:
        os.system("start steam://open/main")
        subprocess.run("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)", shell=True, capture_output=True)
        for _ in range(10): pyautogui.press("volumeup")
        return "Game mode ON! Steam open, brightness full, volume badha diya. Have fun, Master!"
    except Exception as e:
        log.error(f"Gaming mode failed: {e}")
        return "Gaming mode me thodi dikkat aayi."

def set_volume(action: str) -> str:
    try:
        if "up" in action or "increase" in action:
            for _ in range(5): pyautogui.press("volumeup")
            return "Volume badha diya hai."
        elif "down" in action or "decrease" in action:
            for _ in range(5): pyautogui.press("volumedown")
            return "Volume kam kar diya hai."
        elif "mute" in action:
            pyautogui.press("volumemute")
            return "Volume mute kar diya hai."
        return "Volume command samajh nahi aayi."
    except Exception as e:
        return f"Volume control fail: {e}"

def set_brightness(level: int) -> str:
    try:
        subprocess.run(f"powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})", shell=True, capture_output=True)
        return f"Brightness {level}% kar di hai."
    except Exception as e:
        return f"Brightness set nahi kar payi: {e}"

def read_selected_text() -> str:
    try:
        # Clipboard ko khaali kar do (taaki purana text na padhe)
        pyperclip.copy("")
        
        # Text ko copy karne ke liye Ctrl+C dabao
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3) # Wait for clipboard to update
        
        # Clipboard se text uthao
        selected_text = pyperclip.paste()
        
        if not selected_text or not selected_text.strip():
            return "Ayuu, tune koi text select nahi kiya hai. Pehle mouse se text highlight karo."
            
        # Agar text bahut lamba hai, toh sirf pehle 400 characters bolo
        text_to_read = selected_text.strip().replace("\n", " ")
        return f"Selected text yeh hai: {text_to_read}"
        
    except Exception as e:
        return f"Selected text read nahi kar payi: {e}"

def set_timer(seconds: int, tts_callback) -> str:
    def timer_thread():
        time.sleep(seconds)
        tts_callback(f"Ayuu, tera {seconds} second ka timer khatam ho gaya!")
        os.system("start https://www.youtube.com/watch?v=2R0Z3F9o76g") # Alarm sound (optional)
        
    threading.Thread(target=timer_thread, daemon=True).start()
    return f"{seconds} second ka timer laga diya hai."