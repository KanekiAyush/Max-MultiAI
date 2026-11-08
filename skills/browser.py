"""Browser automation for MAX using regular Chrome (Fast & Lightweight)."""
import subprocess
import urllib.parse
from utils.logger import get_logger

log = get_logger("MAX.Skills.Browser")

# Tera Chrome ka path aur profile
CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
PROFILE_DIR = "Default"

def _open_url(url: str) -> bool:
    """Chrome me naya tab kholta hai bina existing tabs ko chhede."""
    try:
        # subprocess use kar rahe hain taaki Chrome background me na ruke
        subprocess.Popen([CHROME_PATH, f"--profile-directory={PROFILE_DIR}", url])
        return True
    except Exception as e:
        log.error(f"Failed to open URL: {e}")
        return False

def search_google(query: str) -> str:
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    if _open_url(url):
        return f"Google pe {query} search kar diya hai."
    return "Chrome open nahi kar payi."

def play_on_youtube(query: str) -> str:
    if not query:
        _open_url("https://www.youtube.com")
        return "YouTube open kar diya hai."
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    if _open_url(url):
        return f"YouTube pe {query} search kar diya hai. Pehla video tu play kar lena."
    return "YouTube open nahi kar payi."

def open_whatsapp_web() -> str:
    if _open_url("https://web.whatsapp.com"):
        return "WhatsApp Web open kar rahi hoon."
    return "WhatsApp Web open nahi kar payi."