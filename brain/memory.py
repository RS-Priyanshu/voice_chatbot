import os
from typing import List, Dict, Any
from config.settings import settings
from utils.helpers import load_json, save_json

class Memory:
    def __init__(self):
        self._file = settings.MEMORY_FILE
        self.conversations: List[Dict[str, str]] = self._load()

    def _load(self) -> List[Dict[str, str]]:
        data = load_json(self._file, {"history": []})
        return data.get("history", [])

    def add(self, role: str, content: str):
        self.conversations.append({"role": role, "content": content})
        self._persist()

    def get_context(self, window: int = 10) -> List[Dict[str, str]]:
        return self.conversations[-window:]

    def clear(self):
        self.conversations = []
        self._persist()

    def _persist(self):
        save_json(self._file, {"history": self.conversations})

    @property
    def is_first_launch(self) -> bool:
        return not os.path.exists(settings.USER_NAME_FILE)