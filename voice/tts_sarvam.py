# voice/tts_sarvam.py
import base64
import io
import wave
import numpy as np
import requests
import threading
# import json  # ✅ Keep if you need it for debugging
from config.settings import settings
from utils.logger import logger
from core.event_bus import event_bus
# from sarvamai import SarvamAI  # ❌ REMOVE: You're not using the SDK, just raw requests

class SarvamTTS:
    def __init__(self, audio_player):
        self.player = audio_player
        self.base_url = "https://api.sarvam.ai/text-to-speech"  # ✅ Correct
        self.headers = {
            "api-subscription-key": settings.SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        self._stop_event = threading.Event()
        logger.info(f"Sarvam TTS initialized | Model: {settings.SARVAM_TTS_MODEL}, Speaker: {settings.SARVAM_TTS_SPEAKER}")

    def speak(self, text: str):
        if not text.strip(): 
            return
        self._stop_event.clear()
        threading.Thread(target=self._generate_and_play, args=(text,), daemon=True).start()

    def stop(self):
        self._stop_event.set()
        self.player.stop()

    def _generate_and_play(self, text: str):
        # ✅ CORRECT PAYLOAD: Use "text" (string), NOT "inputs"
        payload = {
            "text": text,  # ✅ FIXED: Was "inputs", must be "text"
            "target_language_code": settings.SARVAM_TTS_LANG,
            "speaker": settings.SARVAM_TTS_SPEAKER,
            "model": settings.SARVAM_TTS_MODEL,
            "output_format": "wav",
            # "enable_preprocessing": True  # ❌ REMOVE: Not supported for bulbul:v3 [[12]]
        }
        
        # ✅ OPTIONAL: Add model-specific params
        if settings.SARVAM_TTS_MODEL == "bulbul:v3":
            payload["pace"] = 1.0  # Range: 0.5-2.0 for v3
            payload["temperature"] = 0.6  # Range: 0.01-2.0, v3 only
        # For bulbul:v2, you could add pitch/loudness instead
        
        try:
            event_bus.emit("state_change", state="speaking")
            resp = requests.post(
                self.base_url, 
                json=payload, 
                headers=self.headers, 
                timeout=30
            )
            
            # ✅ Enhanced error logging
            if resp.status_code == 404:
                logger.error(f" Sarvam 404: Endpoint not found. URL: {self.base_url}")
                logger.error(f"   Payload sent: {payload}")  # Debug help
                event_bus.emit("error", msg="Voice configuration error (404).")
                return
            if resp.status_code == 401:
                logger.error(" Sarvam 401: Invalid API Key")
                event_bus.emit("error", msg="Voice API key is invalid.")
                return
            if resp.status_code == 400:
                try:
                    error_data = resp.json()
                    logger.error(f" Sarvam 400: {error_data}")
                    event_bus.emit("error", msg=f"Voice error: {error_data.get('error', {}).get('message')}")
                except:
                    logger.error(f" Sarvam 400: {resp.text}")
                return
                
            resp.raise_for_status()
            data = resp.json()
            
            # ✅ Handle response: Sarvam returns "audios" array [[12]]
            audio_list = data.get("audios", [])
            if not audio_list:
                logger.error(f" Sarvam: No audio in response. Full response: {data}")
                event_bus.emit("error", msg="Voice service returned no audio.")
                return
            
            audio_b64 = audio_list[0]
            audio_bytes = base64.b64decode(audio_b64)
            
            # Decode WAV to Numpy
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                raw = wf.readframes(wf.getnframes())
                audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

            # Stream playback
            chunk_size = 8192
            for i in range(0, len(audio_np), chunk_size):
                if self._stop_event.is_set(): 
                    break
                chunk = audio_np[i:i+chunk_size]
                vol = float(np.mean(np.abs(chunk)))
                self.player.volume_callback(vol)
                self.player.feed_audio(chunk)

            if not self._stop_event.is_set():
                self.player.volume_callback(0.0)
                event_bus.emit("tts_finished")

        except requests.exceptions.Timeout:
            logger.error(" Sarvam TTS: Request timed out")
            event_bus.emit("error", msg="Voice service timeout.")
        except requests.exceptions.ConnectionError:
            logger.error(" Sarvam TTS: Connection error")
            event_bus.emit("error", msg="Cannot connect to voice service.")
        except Exception as e:
            logger.error(f" Sarvam TTS failed: {type(e).__name__}: {e}")
            event_bus.emit("error", msg="Voice service unavailable.")