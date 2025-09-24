# modules/voice.py
import threading
import queue
import time
import os
import tempfile
import asyncio

try:
    import edge_tts  # pip install edge-tts
    from playsound import playsound  # pip install playsound==1.2.2
    _ok = True
except Exception:
    edge_tts = None
    playsound = None
    _ok = False

_tts_queue = queue.Queue()
_worker_started = False
_default_rate = 170  # our "human-ish" baseline
_cached_voices = []  # list of dicts from edge-tts (ShortName, Gender, Locale, etc.)
_current_voice = "en-US-AriaNeural"  # good default; we'll auto-switch to Zira/Guy if available

def is_available():
    return _ok and (edge_tts is not None) and (playsound is not None)

def _rate_to_pct(rate_int: int) -> str:
    """
    Edge TTS expects rate as a percentage string like '+10%' or '-20%'.
    We'll map 170 -> '+0%'. Clamp around 100–250.
    """
    try:
        r = int(rate_int)
    except Exception:
        r = _default_rate
    r = max(100, min(250, r))
    pct = int(round((r - 170) / 170 * 100))  # rough mapping
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"

def list_voices():
    """Returns a simplified list of (ShortName, Locale, Gender)."""
    out = []
    for v in _cached_voices:
        out.append((v.get("ShortName", ""), v.get("Locale", ""), v.get("Gender", "")))
    return out

def set_voice_by_name(name_substring: str):
    """Pick a voice whose ShortName or FriendlyName contains the substring."""
    global _current_voice
    if not is_available() or not _cached_voices:
        return False
    ns = (name_substring or "").lower()
    for v in _cached_voices:
        short = v.get("ShortName", "")
        friendly = v.get("FriendlyName", "")
        if ns in short.lower() or ns in friendly.lower():
            _current_voice = short
            return True
    return False

def configure(rate=None, voice_hint=None):
    """Store defaults; worker uses them at speak-time."""
    global _default_rate
    if rate is not None:
        try:
            _default_rate = int(rate)
        except Exception:
            pass
    # voice_hint handled in start_worker once voices are loaded

async def _load_voices():
    """Fetch and cache available voices from Edge TTS."""
    global _cached_voices, _current_voice
    try:
        _cached_voices = await edge_tts.list_voices()
        # Prefer familiar voices if present
        preferred = ["en-US-ZiraNeural", "en-US-GuyNeural", "en-US-AriaNeural", "en-US-DavisNeural"]
        for p in preferred:
            if any(v.get("ShortName") == p for v in _cached_voices):
                _current_voice = p
                break
    except Exception:
        _cached_voices = []

async def _synthesize_to_file(text: str, voice: str, rate_pct: str, out_path: str):
    """Use Edge TTS to synthesize text to an mp3 file."""
    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate_pct)
    await communicator.save(out_path)

def _worker(voice_hint=None):
    # Each thread needs its own asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Load voices once
    loop.run_until_complete(_load_voices())

    # If user gave a hint (e.g., "zira"), try to set it
    if voice_hint:
        set_voice_by_name(voice_hint)

    while True:
        item = _tts_queue.get()
        if item is None:
            break
        text, rate, done_evt = item
        try:
            rate_pct = _rate_to_pct(rate if rate is not None else _default_rate)
            # temp mp3 file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
                tmp_path = tf.name
            # synthesize
            loop.run_until_complete(_synthesize_to_file(str(text), _current_voice, rate_pct, tmp_path))
            # play (blocking)
            playsound(tmp_path)
        except Exception:
            pass
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            if done_evt is not None:
                try:
                    done_evt.set()
                except Exception:
                    pass
        time.sleep(0.02)

def start_worker(default_rate=170, voice_hint=None):
    """Start the single TTS worker once."""
    global _worker_started, _default_rate
    if not is_available() or _worker_started:
        return
    _default_rate = int(default_rate)
    t = threading.Thread(target=_worker, kwargs={"voice_hint": voice_hint}, daemon=True)
    t.start()
    _worker_started = True

def speak(text, rate=None):
    """Non-blocking: enqueue for worker thread."""
    if not is_available():
        return
    _tts_queue.put((text, rate, None))

def speak_blocking(text, rate=None, timeout=15.0):
    """Blocking, but still uses the worker. Useful for diagnostics."""
    if not is_available():
        return False
    done = threading.Event()
    _tts_queue.put((text, rate, done))
    return done.wait(timeout=timeout)

def beep():
    try:
        import winsound
        winsound.Beep(800, 300)
    except Exception:
        pass
