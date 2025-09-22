# modules/reminders.py
import json
import os
import time
import threading
import re
from datetime import datetime, timedelta

REMINDER_PATH = os.path.join("data", "reminders.json")

def _now():
    return datetime.now()

def _now_str():
    return _now().strftime("%Y-%m-%d %H:%M:%S")

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
        # normalize
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

# -------- Day 8 simple text reminder --------
def add_text_reminder(text):
    reminders = load_reminders()
    reminders.append({"task": text, "remind_at": None})
    save_reminders(reminders)

# -------- Day 9 timed (seconds) reminder --------
def add_timed_reminder(task, seconds_from_now):
    reminders = load_reminders()
    remind_at_dt = _now() + timedelta(seconds=seconds_from_now)
    remind_at = remind_at_dt.strftime("%Y-%m-%d %H:%M:%S")
    reminders.append({"task": task, "remind_at": remind_at})
    save_reminders(reminders)
    return remind_at

# -------- Day 10 clock-time parsing --------
def parse_time_to_today(time_str: str) -> datetime:
    """
    Accepts things like:
      - '8:30 pm', '8 pm', '08:30 pm'
      - '07:10', '7:10', '19:45' (24h)
      - '7 am', '7:00 am'
    Returns a datetime set to today (or tomorrow if time already passed today).
    """
    s = time_str.strip().lower()
    now = _now()
    today = now.date()

    # Remove extra words like "at"
    if s.startswith("at "):
        s = s[3:].strip()

    # Try patterns with am/pm
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)$", s)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        mer = m.group(3)
        if mer == "pm" and hh != 12:
            hh += 12
        if mer == "am" and hh == 12:
            hh = 0
        dt = datetime(now.year, now.month, now.day, hh, mm, 0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt

    m = re.match(r"^(\d{1,2})\s*(am|pm)$", s)
    if m:
        hh = int(m.group(1))
        mer = m.group(2)
        mm = 0
        if mer == "pm" and hh != 12:
            hh += 12
        if mer == "am" and hh == 12:
            hh = 0
        dt = datetime(now.year, now.month, now.day, hh, mm, 0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt

    # 24-hour with minutes: 19:30 or 7:05
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        dt = datetime(now.year, now.month, now.day, hh, mm, 0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt

    # Just hour (24h assumption)
    m = re.match(r"^(\d{1,2})$", s)
    if m:
        hh = int(m.group(1))
        mm = 0
        dt = datetime(now.year, now.month, now.day, hh, mm, 0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt

    raise ValueError("Unrecognized time format")

def add_clock_reminder(task: str, time_str: str):
    """Add reminder for a specific clock time like '8:30 pm' or '07:10'."""
    dt = parse_time_to_today(time_str)
    remind_at = dt.strftime("%Y-%m-%d %H:%M:%S")
    reminders = load_reminders()
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
            now_str = _now_str()
            remaining = []
            for r in reminders:
                due_time = r.get("remind_at")
                if due_time and due_time <= now_str:
                    try:
                        callback(r["task"])
                    except Exception:
                        pass  # never crash the checker
                else:
                    remaining.append(r)
            if len(remaining) != len(reminders):
                save_reminders(remaining)
            time.sleep(1)
    t = threading.Thread(target=run, daemon=True)
    t.start()
