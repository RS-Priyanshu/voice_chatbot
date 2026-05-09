import numpy as np
import sounddevice as sd
import threading
import queue
from utils.logger import logger

class AudioPlayer:
    def __init__(self, sample_rate=16000):
        self.sr = sample_rate
        self.buffer = queue.Queue()
        self._stop_event = threading.Event()
        self._playback_thread = None
        self.volume_callback = lambda vol: None

    def feed_audio(self, chunk):
        """Accepts numpy array or raw bytes"""
        if isinstance(chunk, bytes):
            chunk = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
        self.buffer.put(chunk)

    def start(self):
        if self._playback_thread and self._playback_thread.is_alive():
            return
        self._stop_event.clear()
        self._playback_thread = threading.Thread(target=self._play_loop, daemon=True)
        self._playback_thread.start()

    def stop(self):
        self._stop_event.set()
        self.buffer = queue.Queue()

    def _play_loop(self):
        stream = sd.OutputStream(samplerate=self.sr, channels=1, dtype=np.float32)
        stream.start()
        try:
            while not self._stop_event.is_set():
                try:
                    chunk = self.buffer.get(timeout=0.5)
                    vol = float(np.mean(np.abs(chunk)))
                    self.volume_callback(max(0.0, min(1.0, vol)))
                    stream.write(chunk)
                except queue.Empty:
                    continue
        finally:
            stream.stop()
            stream.close()
            self.volume_callback(0.0)