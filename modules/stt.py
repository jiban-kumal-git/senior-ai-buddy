# modules/stt.py
import os
import queue
import json
import sounddevice as sd

# ---- (optional) Offline Vosk bits kept, but you can ignore if using online only ----
try:
    from vosk import Model, KaldiRecognizer
    _vosk_ok = True
except Exception:
    _vosk_ok = False

DEFAULT_MODEL_PATH = os.path.join("models", "vosk-en")

def has_offline_model(model_path: str = DEFAULT_MODEL_PATH) -> bool:
    return _vosk_ok and os.path.isdir(model_path) and os.path.exists(os.path.join(model_path, "am"))

def transcribe_offline(seconds: int = 5, model_path: str = DEFAULT_MODEL_PATH, samplerate: int = 16000) -> str:
    if not _vosk_ok or not has_offline_model(model_path):
        return ""
    model = Model(model_path)
    rec = KaldiRecognizer(model, samplerate)
    rec.SetWords(False)

    q = queue.Queue()
    def callback(indata, frames, time, status):
        if status:
            pass
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype="int16",
                           channels=1, callback=callback):
        sd.sleep(int(seconds * 1000))
        # drain queue
        while not q.empty():
            data = q.get()
            rec.AcceptWaveform(data)
    try:
        res = json.loads(rec.FinalResult())
        return (res.get("text") or "").strip().lower()
    except Exception:
        return ""

# ---- ONLINE: Google STT via SpeechRecognition, but mic recording via sounddevice (no PyAudio needed) ----
def transcribe_online(seconds: int = 5, samplerate: int = 16000) -> str:
    """
    Records 'seconds' from default microphone using sounddevice,
    then feeds raw audio to SpeechRecognition's Google recognizer.
    Avoids needing PyAudio.
    """
    try:
        import numpy as np  # sounddevice typically needs numpy; should already be installed
        import speech_recognition as sr
    except Exception:
        return ""

    # Record audio (mono int16) with sounddevice
    rec = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()  # blocking until recording finishes
    # Convert to raw bytes
    audio_bytes = rec.tobytes()

    # Build SpeechRecognition AudioData (sample_width=2 bytes for int16)
    audio_data = sr.AudioData(audio_bytes, samplerate, 2)

    # Recognize with Google
    try:
        text = sr.Recognizer().recognize_google(audio_data)
        return (text or "").strip().lower()
    except Exception:
        return ""
