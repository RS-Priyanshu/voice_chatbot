from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

def find_env_file() -> Path:
    settings_dir = Path(__file__).parent
    candidates = [
        settings_dir.parent / ".env",
        Path.cwd() / ".env",
        Path(__file__).parent.parent.parent / ".env",
    ]
    for p in candidates:
        if p.exists(): return p
    return Path(".env")

env_path = find_env_file()
load_dotenv(dotenv_path=env_path, override=True)

class Settings(BaseSettings):
    # Sarvam AI TTS
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    SARVAM_TTS_MODEL: str = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
    SARVAM_TTS_SPEAKER: str = os.getenv("SARVAM_TTS_SPEAKER", "simran")
    SARVAM_TTS_LANG: str = os.getenv("SARVAM_TTS_LANG", "en-IN")
    SARVAM_TTS_SAMPLE_RATE: int = int(os.getenv("SARVAM_TTS_SAMPLE_RATE", "24000"))

    # Google Gemini (REST API)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    SYSTEM_PROMPT: str = (
        "You are a smart, concise, and action-oriented AI assistant. "
        "Respond naturally. Keep responses under 2 sentences unless detailed explanation is requested. "
        "If asked to perform an action, prefix with [CMD:] followed by the intent."
    )

    # Audio & STT
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "tiny")
    VAD_THRESHOLD: float = float(os.getenv("VAD_THRESHOLD", "0.025"))
    SILENCE_DURATION_SEC: float = float(os.getenv("SILENCE_DURATION_SEC", "0.5"))
    MIN_SPEECH_DURATION_SEC: float = float(os.getenv("MIN_SPEECH_DURATION_SEC", "0.3"))

    MEMORY_FILE: str = "data/conversation_history.json"
    USER_NAME_FILE: str = "data/user_name.txt"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        case_sensitive = False
        extra = "ignore"

    def validate_keys(self) -> tuple[bool, list[str]]:
        errors = []
        if not self.SARVAM_API_KEY or len(self.SARVAM_API_KEY) < 10:
            errors.append("SARVAM_API_KEY is missing or invalid")
        if not self.GOOGLE_API_KEY or len(self.GOOGLE_API_KEY) < 10:
            errors.append("GOOGLE_API_KEY is missing or invalid")
        return len(errors) == 0, errors

settings = Settings()