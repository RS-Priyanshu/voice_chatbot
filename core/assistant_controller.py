# core/assistant_controller.py
import os, time, threading, webbrowser, subprocess
from utils.logger import logger
from config.settings import settings
from brain.memory import Memory
from brain.ai_engine import AIEngine
from voice.stt import STT
from voice.tts_sarvam import SarvamTTS
from voice.audio_player import AudioPlayer
from core.event_bus import event_bus
from utils.helpers import load_user_name, extract_command
from ui.animations import FaceState

class AssistantController:
    def __init__(self, ui_face):
        self.ui = ui_face
        self.memory = Memory()
        self.audio_player = AudioPlayer()
        self.audio_player.volume_callback = self.ui.set_volume
        self.stt = STT()
        self.tts = SarvamTTS(self.audio_player)
        self.ai = AIEngine(self.memory)
        self._setup_event_bus()

    def _setup_event_bus(self):
        event_bus.subscribe("state_change", self._on_state_change)
        event_bus.subscribe("text_received", self._on_user_input)
        event_bus.subscribe("tts_finished", self._on_tts_finished)
        event_bus.subscribe("command_detected", self._on_command)
        event_bus.subscribe("error", self._on_error)
        self.audio_player.start()

    def _on_state_change(self, state: str):
        state_enum = FaceState(state)
        self.ui.set_state(state_enum)
        self.stt.set_speaking(state_enum == FaceState.SPEAKING)
        if state_enum == FaceState.SPEAKING:
            self.audio_player.start()

    def _on_user_input(self, text: str):
        threading.Thread(target=self._process_input, args=(text,), daemon=True).start()

    def _process_input(self, text: str):
        event_bus.emit("state_change", state="thinking")
        reply = self.ai.chat(text)
        cmd, clean_reply = extract_command(reply)
        self.audio_player.start()
        self.tts.speak(clean_reply)
        if cmd:
            self.ai.execute_command(cmd)

    def _on_tts_finished(self):
        event_bus.emit("state_change", state="idle")
        self.stt.start_listening()

    def _on_command(self, cmd: str):
        logger.info(f"Executing command: {cmd}")
        try:
            if "youtube" in cmd:
                webbrowser.open("https://www.youtube.com")
            elif "search" in cmd or "google" in cmd:
                q = cmd.replace("search", "").replace("google", "").strip()
                webbrowser.open(f"https://www.google.com/search?q={q}")
            elif "vs code" in cmd or "vscode" in cmd:
                subprocess.Popen(["code"], shell=True)
            elif "clear memory" in cmd:
                self.memory.clear()
                self.tts.speak("Memory cleared.")
        except Exception as e:
            logger.error(f"Command execution failed: {e}")

    def _on_error(self, msg: str):
        self.ui.set_state(FaceState.ERROR)
        try:
            self.tts.speak(msg)
        except Exception:
            logger.warning(f"Failed to speak error: {msg}")
        threading.Thread(target=self._recover_from_error, daemon=True).start()

    def _recover_from_error(self):
        time.sleep(2.5)
        event_bus.emit("state_change", state="idle")
        self.stt.start_listening()

    def greet_user(self):
        name = load_user_name(settings.USER_NAME_FILE)
        if not name:
            self.tts.speak("Helloboss! welcom back!  tell me what should i have to do now should i turn onn the today's current news or start the I P L match")
            return
        hour = time.localtime().tm_hour
        greeting = "Good morning" if hour < 12 else "Good evening"
        self.tts.speak(f"{greeting}, {name}. What should we work on today?")

    def handle_interrupt(self):
        self.tts.stop()
        if self.memory.conversations:
            self.memory.conversations.pop()
        self.stt.start_listening(skip_if_speaking=False)