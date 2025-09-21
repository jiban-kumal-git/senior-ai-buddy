# modules/reminders.py
import json
import os

REMINDER_PATH = os.path.join("data", "reminders.json")

def load_reminders():
    """Load reminders from JSON file, or return empty list if none exist."""
    if not os.path.exists(REMINDER_PATH):
        save_reminders([])
        return []
    try:
        with open(REMINDER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        save_reminders([])
        return []

def save_reminders(reminders):
    """Save list of reminders to JSON file."""
    with open(REMINDER_PATH, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

def add_reminder(text):
    reminders = load_reminders()
    reminders.append(text)
    save_reminders(reminders)

def clear_reminders():
    save_reminders([])
