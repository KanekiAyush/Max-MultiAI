"""Browser automation skills for MAX."""
import webbrowser
from utils.logger import get_logger

log = get_logger("MAX.Skills.Browser")

def open_website(url: str) -> str:
    log.info(f"Opening URL: {url}")
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Website open kar di hai."

def play_on_youtube(query: str) -> str:
    log.info(f"YouTube search: {query}")
    if not query:
        webbrowser.open("https://www.youtube.com")
        return "YouTube open kar diya hai."
        
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"YouTube pe {query} search kar diya hai."

def search_google(query: str) -> str:
    log.info(f"Google search: {query}")
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Google pe search kar diya hai."