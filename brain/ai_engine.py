# brain/ai_engine.py
import time
import requests
import json
from config.settings import settings
from utils.logger import logger
from core.event_bus import event_bus

class AIEngine:
    def __init__(self, memory):
        self.memory = memory
        # Correct endpoint & model name [[12]][[17]]
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
        logger.info(f"Gemini AI Engine initialized (REST): {settings.GEMINI_MODEL}")

    def chat(self, user_input: str) -> str:
        context = self.memory.get_context()
        
        # Build Gemini-compatible message history
        contents = []
        for msg in context:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": user_input}]})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 256,
                "topP": 0.95,
                "topK": 40
            },
            "systemInstruction": {
                "parts": [{"text": settings.SYSTEM_PROMPT}]
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GOOGLE_API_KEY
        }
        
        try:
            start = time.time()
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=20)
            
            if resp.status_code == 404:
                logger.error(f"Model not found: {settings.GEMINI_MODEL}")
                return f"Model '{settings.GEMINI_MODEL}' not available. Please check your configuration."
            if resp.status_code == 400:
                error_data = resp.json()
                logger.error(f"Gemini bad request: {error_data}")
                return "I didn't understand that request. Please try rephrasing."
            if resp.status_code == 429:
                logger.error("Gemini quota exceeded")
                return "I'm getting too many requests. Please wait a moment and try again."
            if resp.status_code == 403:
                logger.error("Gemini API key invalid")
                return "API access denied. Please check your Google API key in .env"
                
            resp.raise_for_status()
            elapsed = time.time() - start
            logger.info(f"Gemini response in {elapsed:.2f}s")
            
            data = resp.json()
            # Safe extraction of response text
            candidates = data.get("candidates", [])
            if not candidates:
                return "I didn't have a response for that."
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            
            if not text:
                text = "I didn't have a response for that. Could you rephrase?"
            
            self.memory.add("user", user_input)
            self.memory.add("assistant", text)
            return text
            
        except requests.exceptions.Timeout:
            logger.error("Gemini request timed out")
            return "I'm taking too long to think. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini network error: {e}")
            return "I lost connection to my brain. Please check your internet."
        except Exception as e:
            logger.error(f"Unexpected AI Engine error: {e}")
            return "Something went wrong on my end. Please try again."

    def execute_command(self, command: str):
        event_bus.emit("command_detected", cmd=command)