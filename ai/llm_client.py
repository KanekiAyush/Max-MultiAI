"""LLM Client for MAX using Groq API."""
import os
from groq import Groq
from utils.logger import get_logger

log = get_logger("MAX.LLM")

class LLMClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            log.warning("GROQ_API_KEY not found in .env file.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            self.model = "openai/gpt-oss-20b" # Groq ka naya fast free model

    def get_response(self, prompt: str) -> str:
        if not self.client:
            return "Ayuu, meri API key nahi mili. Please .env file check karo."

        try:
            log.info("Calling Groq API...")
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are MAX, a witty and humorous female AI assistant created by Ayush. Keep your answers short, conversational, and in Hinglish (Hindi + English) unless asked otherwise. Call the user 'Ayuu' occasionally. Be sassy but helpful."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=150, # Chhote jawab taaki TTS fast bole
            )
            reply = chat_completion.choices[0].message.content.strip()
            return reply
        except Exception as e:
            log.error(f"Groq API Error: {e}")
            return "Ayuu, mera dimaag abhi thoda hang ho gaya hai. Network check karo ya thodi der baad try karna."

# Singleton instance
llm = LLMClient()