"""Smart LLM Client: Ollama (Local) First, Cloud API (Groq/OpenRouter) Fallback."""
import os
import sqlite3
import hashlib
import ollama
from groq import Groq
from openai import OpenAI
from utils.logger import get_logger
from pathlib import Path

log = get_logger("MAX.LLM")
DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"

class LLMClient:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        # Cloud Clients (Sirf zaroorat padne par use honge)
        self.groq_client = Groq(api_key=self.groq_key, timeout=10.0) if self.groq_key else None
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_key,
            timeout=10.0
        ) if self.openrouter_key else None

        self.system_prompt = "You are MAX, a witty and humorous female AI assistant. Always answer the user's questions directly. If asked for a joke, tell a short, funny joke. Keep responses brief and conversational in Hinglish."
        self.offline_model = "qwen2.5:1.5b" # Ollama local model

    def _get_cache(self, prompt: str) -> str:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS llm_cache (query_hash TEXT PRIMARY KEY, response TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        query_hash = hashlib.md5(prompt.encode()).hexdigest()
        c.execute("SELECT response FROM llm_cache WHERE query_hash = ?", (query_hash,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

    def _save_cache(self, prompt: str, response: str):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query_hash = hashlib.md5(prompt.encode()).hexdigest()
        c.execute("INSERT OR REPLACE INTO llm_cache (query_hash, response) VALUES (?, ?)", (query_hash, response))
        conn.commit()
        conn.close()

    def get_response(self, prompt: str, use_cache=True) -> str:
        # 1. Cache Check (0 Tokens)
        if use_cache:
            cached_response = self._get_cache(prompt)
            if cached_response:
                log.info("⚡ Retrieved from Cache!")
                return cached_response

        # 2. Ollama Local Brain (Unlimited Tokens, No Internet Needed)
        try:
            log.info(f"Calling Local Ollama ({self.offline_model})...")
            response = ollama.chat(model=self.offline_model, messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': prompt},
            ])
            reply = response['message']['content'].strip()
            
            # Agar Ollama ne kuch bakwas nahi kiya (empty response nahi hai), toh cache me save karo
            if reply and len(reply) > 5:
                self._save_cache(prompt, reply)
                return reply
        except Exception as e:
            log.warning(f"Ollama failed: {e}. Trying Cloud APIs...")

        # 3. Cloud Fallback (Groq -> OpenRouter) - Agar Ollama band ho ya fail ho jaye
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        if self.groq_client:
            try:
                log.info("Calling Groq API (Fallback)...")
                completion = self.groq_client.chat.completions.create(
                    messages=messages,
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    max_tokens=150,
                )
                reply = completion.choices[0].message.content.strip()
                self._save_cache(prompt, reply)
                return reply
            except Exception as e:
                log.error(f"Groq failed: {e}")

        if self.openrouter_client:
            try:
                log.info("Calling OpenRouter API (Fallback)...")
                completion = self.openrouter_client.chat.completions.create(
                    model="meta-llama/llama-3.3-70b-instruct:free",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150,
                )
                reply = completion.choices[0].message.content.strip()
                self._save_cache(prompt, reply)
                return reply
            except Exception as e:
                log.error(f"OpenRouter failed: {e}")

        return "Ayuu, mera local dimaag (Ollama) aur internet dono abhi kaam nahi kar rahe. Please check karo."

llm = LLMClient()