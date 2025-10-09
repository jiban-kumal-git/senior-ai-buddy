# modules/stt.py
import os
import json
import queue
import wave
import numpy as np
import sounddevice as sd

# -----------------------------
# Optional OFFLINE: Vosk bits
# -----------------------------
try:
    from vosk import Model, KaldiRecognizer
    _vosk_ok = True
except Exception:
    _vosk_ok = False

DEFAULT_MODEL_PATH = os.path.join("models", "vosk-en")

def has_offline_model(model_path=DEFAULT_MODEL_PATH):
    """Return True if a Vosk model folder seems valid."""
    try:
        return (
            _vosk_ok and
            os.path.isdir(model_path) and
            os.path.exists(os.path.join(model_path, "am"))
        )
    except Exception:
        return False

def transcribe_offline(seconds=5, model_path=DEFAULT_MODEL_PATH, samplerate=16000):
    """
    Record mic audio for <seconds> and recognize with Vosk (offline).
    Returns lowercased text or "" if unavailable.
    """
    if not _vosk_ok or not has_offline_model(model_path):
        return ""

    model = Model(model_path)
    rec = KaldiRecognizer(model, samplerate)
    rec.SetWords(False)

    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            # You can print(status) for debug if you want
            pass
        q.put(bytes(indata))

    try:
        with sd.RawInputStream(
            samplerate=samplerate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback,
            device=_input_device_index
        ):
            sd.sleep(int(seconds * 1000))
            while not q.empty():
                data = q.get()
                rec.AcceptWaveform(data)
        try:
            res = json.loads(rec.FinalResult())
            return (res.get("text") or "").strip().lower()
        except Exception:
            return ""
    except Exception:
        return ""

# -----------------------------
# Mic device helpers (Day 14)
# -----------------------------
_input_device_index = None  # None = system default

def list_input_devices():
    """Return list of (index, name) for devices that have input channels."""
    out = []
    try:
        devs = sd.query_devices()
        for i, d in enumerate(devs):
            if d.get("max_input_channels", 0) > 0:
                out.append((i, d.get("name", f"Device {i}")))
    except Exception:
        pass
    return out

def set_input_device(index):
    """
    Set the input device by index. Pass None to reset to system default.
    Returns True on success, False otherwise.
    """
    global _input_device_index
    if index is None:
        _input_device_index = None
        return True
    try:
        index = int(index)
        info = sd.query_devices(index)
        if info.get("max_input_channels", 0) > 0:
            _input_device_index = index
            return True
    except Exception:
        pass
    return False

def _get_default_input_samplerate():
    """Try to use the device's default input samplerate, else fall back to 16000."""
    try:
        if _input_device_index is not None:
            info = sd.query_devices(_input_device_index, 'input')
        else:
            info = sd.query_devices(None, 'input')
        sr = int(info.get('default_samplerate', 16000))
        # keep it sane
        return max(8000, min(48000, sr))
    except Exception:
        return 16000

def mic_test(seconds=3, filename="mic_test.wav"):
    """
    Record a short clip and save it to WAV so you can hear what we captured.
    Returns the absolute file path.
    """
    sr = _get_default_input_samplerate()
    try:
        audio = sd.rec(
            int(seconds * sr),
            samplerate=sr,
            channels=1,
            dtype="int16",
            device=_input_device_index
        )
        sd.wait()
    except Exception:
        return os.path.abspath(filename)

    data = audio.tobytes()
    try:
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # int16
            wf.setframerate(sr)
            wf.writeframes(data)
    except Exception:
        pass
    return os.path.abspath(filename)

# -----------------------------
# ONLINE STT (Google via SR)
# -----------------------------
def transcribe_online(seconds=5):
    """
    Record 'seconds' from selected/default mic using sounddevice (int16 mono),
    then feed to SpeechRecognition's Google recognizer.
    Returns lowercased text or "" on failure.
    """
    try:
        import speech_recognition as sr
    except Exception:
        return ""

    sr_hz = _get_default_input_samplerate()

    # Record audio
    try:
        audio = sd.rec(
            int(seconds * sr_hz),
            samplerate=sr_hz,
            channels=1,
            dtype="int16",
            device=_input_device_index
        )
        sd.wait()
    except Exception:
        return ""

    # Light gain if too quiet (rough RMS check)
    data = audio.astype(np.int16)
    rms = float(np.sqrt(np.mean((data.astype(np.float32))**2)) + 1e-9)
    if rms < 200:  # tweak if needed
        data = np.clip(data.astype(np.int32) * 3, -32768, 32767).astype(np.int16)

    # Build SpeechRecognition AudioData
    audio_bytes = data.tobytes()
    try:
        r = sr.Recognizer()
        audio_data = sr.AudioData(audio_bytes, sr_hz, 2)  # 2 bytes/sample for int16
        text = r.recognize_google(audio_data, language="en-US")
        return (text or "").strip().lower()
    except Exception:
        return ""
