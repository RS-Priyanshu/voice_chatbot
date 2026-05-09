import json
import os
import re
import time
from typing import Tuple

def ensure_dir(filepath: str):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

def load_json(filepath: str, default: dict = None) -> dict:
    ensure_dir(filepath)
    if not os.path.exists(filepath):
        return default or {}
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default or {}

def save_json(filepath: str, data: dict):
    ensure_dir(filepath)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def load_user_name(filepath: str) -> str | None:
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        return f.read().strip()

def save_user_name(filepath: str, name: str):
    ensure_dir(filepath)
    with open(filepath, "w") as f:
        f.write(name)

def extract_command(text: str) -> Tuple[str | None, str]:
    match = re.match(r"\[CMD:\s*(.*?)\]", text.strip())
    if match:
        cmd = match.group(1).lower()
        pure_text = text.replace(match.group(0), "").strip()
        return cmd, pure_text
    return None, text