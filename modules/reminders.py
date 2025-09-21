# modules/reminders.py
import json
import os
import time
import threading
from datetime import datetime, timedelta

REMINDER_PATH = os.path.join("data", "reminders.json")

def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_reminders():
    """Load reminders from JSON file; normalize to list of dicts with keys: task, remind_at (or None)."""
    if not os.path.exists(REMINDER_PATH):
        save_reminders([])
        return []
    try:
        with open(REMINDER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = []
        # normalize old simple string reminders to dict form
        fixed = []
        for item in data:
            if isinstance(item, str):
                fixed.append({"task": item, "remind_at": None})
            elif isinstance(item, dict):
                fixed.append({"task": item.get("task", ""), "remind_at": item.get("remind_at")})
        return fixed
    except Exception:
        save_reminders([])
        return []

def save_reminders(reminders):
    """Save list of reminders (list of dicts)."""
    with open(REMINDER_PATH, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

def add_text_reminder(text):
    """Add a simple reminder without time."""
    reminders = load_reminders()
    reminders.append({"task": text, "remind_at": None})
    save_reminders(reminders)

def add_timed_reminder(task, seconds_from_now):
    """Add a timed reminder that should fire after N seconds."""
    reminders = load_reminders()
    remind_at = (datetime.now() + timedelta(seconds=seconds_from_now)).strftime("%Y-%m-%d %H:%M:%S")
    reminders.append({"task": task, "remind_at": remind_at})
    save_reminders(reminders)
    return remind_at

def clear_reminders():
    save_reminders([])

def reminder_checker(callback):
    """Run a background thread that fires callback(task) when reminders are due."""
    def run():
        while True:
            reminders = load_reminders()
            now = _now_str()
            remaining = []
            for r in reminders:
                due_time = r.get("remind_at")
                if due_time and due_time <= now:
                    try:
                        callback(r["task"])
                    except Exception:
                        # never crash the checker
                        pass
                else:
                    remaining.append(r)
            if len(remaining) != len(reminders):
                save_reminders(remaining)
            time.sleep(1)
    t = threading.Thread(target=run, daemon=True)
    t.start()
