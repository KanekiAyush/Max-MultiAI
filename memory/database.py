"""SQLite memory management for MAX."""
import sqlite3
from pathlib import Path
from utils.logger import get_logger

log = get_logger("MAX.Memory")
DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_text TEXT, 
                  max_reply TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_conversation(user_text: str, max_reply: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO conversations (user_text, max_reply) VALUES (?, ?)", (user_text, max_reply))
    conn.commit()
    conn.close()

def get_recent_history(limit=3) -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_text, max_reply FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows[::-1] # Purane se naye ki taraf