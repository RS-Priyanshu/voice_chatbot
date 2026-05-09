import queue
import threading
import numpy as np
import sounddevice as sd
import whisper
from config.settings import settings
from utils.logger import logger
from core.event_bus import event_bus

class STT:
    def __init__(self):
        self.model = whisper.load_model(settings.WHISPER_MODEL)
        self.audio_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._is_speaking = threading.Event()
        self._recording_thread = None
        logger.info(f"Whisper model loaded: {settings.WHISPER_MODEL}")

    def start_listening(self, skip_if_speaking=True):
        if self._is_speaking.is_set() and skip_if_speaking:
            return
        if self._recording_thread and self._recording_thread.is_alive():
            return
        self._stop_event.clear()
        self._recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._recording_thread.start()

    def stop_listening(self):
        self._stop_event.set()
        self.audio_queue.put(None)

    def set_speaking(self, is_speaking: bool):
        if is_speaking:
            self._is_speaking.set()
        else:
            self._is_speaking.clear()

    def _record_loop(self):
        event_bus.emit("state_change", state="listening")
        frames = []
        silence_counter = 0
        silence_threshold = int(settings.SILENCE_DURATION_SEC * 16000 / 512)
        sample_rate = 16000
        chunk_samples = 512

        with sd.InputStream(samplerate=sample_rate, channels=1, dtype=np.float32) as stream:
            while not self._stop_event.is_set():
                chunk, _ = stream.read(chunk_samples)
                rms = np.sqrt(np.mean(chunk**2))

                if rms > settings.VAD_THRESHOLD:
                    frames.append(chunk.flatten())
                    silence_counter = 0
                elif frames:
                    silence_counter += 1
                    if silence_counter > silence_threshold:
                        self._process_segment(frames, sample_rate)
                        frames = []
                        silence_counter = 0

    def _process_segment(self, audio_frames, sr):
        audio = np.concatenate(audio_frames).astype(np.float32)
        duration = len(audio) / sr
        if duration < settings.MIN_SPEECH_DURATION_SEC:
            return

        try:
            result = self.model.transcribe(audio, fp16=False)
            text = result["text"].strip()
            if text:
                logger.info(f"STT Transcription: '{text}'")
                event_bus.emit("text_received", text=text)
            else:
                event_bus.emit("no_speech")
        except Exception as e:
            logger.error(f"STT Error: {e}")