# modules/reminders.py
import json
import os
import time
import threading
import re
from datetime import datetime, timedelta

REMINDER_PATH = os.path.join("data", "reminders.json")

# ---------------- Time helpers ----------------

def _now():
    return datetime.now()

def _now_str():
    return _now().strftime("%Y-%m-%d %H:%M:%S")

def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ---------------- Storage ----------------

def load_reminders():
    """Load reminders from JSON file; normalize to list of dicts with keys:
       task, remind_at (or None), repeat (None or 'daily' or 'weekly:Monday')."""
    if not os.path.exists(REMINDER_PATH):
        save_reminders([])
        return []
    try:
        with open(REMINDER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = []
        fixed = []
        for item in data:
            if isinstance(item, str):
                fixed.append({"task": item, "remind_at": None, "repeat": None})
            elif isinstance(item, dict):
                fixed.append({
                    "task": item.get("task", ""),
                    "remind_at": item.get("remind_at"),
                    "repeat": item.get("repeat", None)
                })
        return fixed
    except Exception:
        save_reminders([])
        return []

def save_reminders(reminders):
    """Save list of reminders (list of dicts)."""
    with open(REMINDER_PATH, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

# ---------------- Day 8: simple text reminder ----------------

def add_text_reminder(text):
    reminders = load_reminders()
    reminders.append({"task": text, "remind_at": None, "repeat": None})
    save_reminders(reminders)

# ---------------- Day 9: timed (seconds) reminder ----------------

def add_timed_reminder(task, seconds_from_now):
    reminders = load_reminders()
    remind_at_dt = _now() + timedelta(seconds=seconds_from_now)
    reminders.append({"task": task, "remind_at": _fmt(remind_at_dt), "repeat": None})
    save_reminders(reminders)
    return _fmt(remind_at_dt)

# ---------------- Day 10: clock-time parsing ----------------

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

    # optional leading 'at '
    if s.startswith("at "):
        s = s[3:].strip()

    # hh:mm am/pm
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)$", s)
    if m:
        hh = int(m.group(1)); mm = int(m.group(2)); mer = m.group(3)
        if mer == "pm" and hh != 12: hh += 12
        if mer == "am" and hh == 12: hh = 0
        dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if dt <= now: dt += timedelta(days=1)
        return dt

    # hh am/pm
    m = re.match(r"^(\d{1,2})\s*(am|pm)$", s)
    if m:
        hh = int(m.group(1)); mer = m.group(2); mm = 0
        if mer == "pm" and hh != 12: hh += 12
        if mer == "am" and hh == 12: hh = 0
        dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if dt <= now: dt += timedelta(days=1)
        return dt

    # 24-hour with minutes: HH:MM
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if m:
        hh = int(m.group(1)); mm = int(m.group(2))
        dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if dt <= now: dt += timedelta(days=1)
        return dt

    # Just hour (24h)
    m = re.match(r"^(\d{1,2})$", s)
    if m:
        hh = int(m.group(1)); mm = 0
        dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if dt <= now: dt += timedelta(days=1)
        return dt

    raise ValueError("Unrecognized time format")

def add_clock_reminder(task: str, time_str: str):
    """One-off reminder for a specific clock time like '8:30 pm' or '07:10'."""
    dt = parse_time_to_today(time_str)
    reminders = load_reminders()
    reminders.append({"task": task, "remind_at": _fmt(dt), "repeat": None})
    save_reminders(reminders)
    return _fmt(dt)

# ---------------- Day 11: recurring rules (daily / weekly) ----------------

_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6
}

def _next_weekday_at_time(target_weekday: int, time_str: str) -> datetime:
    """Return next occurrence of given weekday at clock time (today or future)."""
    now = _now()
    base_time = parse_time_to_today(time_str)  # returns today/tomorrow at that time
    # Align to correct weekday
    days_ahead = (target_weekday - base_time.weekday()) % 7
    dt = base_time + timedelta(days=days_ahead)
    if dt <= now:
        dt += timedelta(days=7)
    return dt

def add_daily_reminder(task: str, time_str: str):
    """Repeat every day at given time."""
    first_dt = parse_time_to_today(time_str)
    reminders = load_reminders()
    reminders.append({"task": task, "remind_at": _fmt(first_dt), "repeat": "daily"})
    save_reminders(reminders)
    return _fmt(first_dt)

def add_weekly_reminder(task: str, weekday_name: str, time_str: str):
    """Repeat every <weekday> at given time. weekday_name e.g. 'monday'."""
    wd = weekday_name.strip().lower()
    if wd not in _WEEKDAYS:
        raise ValueError("Unknown weekday")
    first_dt = _next_weekday_at_time(_WEEKDAYS[wd], time_str)
    reminders = load_reminders()
    reminders.append({"task": task, "remind_at": _fmt(first_dt), "repeat": f"weekly:{wd.capitalize()}"})
    save_reminders(reminders)
    return _fmt(first_dt)

def _advance_reminder(rem):
    """Given a fired reminder with repeat, move it forward and return updated dict; else return None to drop."""
    repeat = rem.get("repeat")
    if not repeat:
        return None
    try:
        current = datetime.strptime(rem["remind_at"], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

    if repeat == "daily":
        next_dt = current + timedelta(days=1)
        rem["remind_at"] = _fmt(next_dt)
        return rem

    if repeat.startswith("weekly:"):
        # Just add 7 days forward
        next_dt = current + timedelta(days=7)
        rem["remind_at"] = _fmt(next_dt)
        return rem

    return None

def clear_reminders():
    save_reminders([])

# ---------------- Background checker ----------------

def reminder_checker(callback):
    """Run a background thread that fires callback(task) when reminders are due.
       Non-repeating reminders are removed. Repeating reminders are re-scheduled."""
    def run():
        while True:
            reminders = load_reminders()
            now_str = _now_str()
            remaining = []
            changed = False

            for r in reminders:
                due_time = r.get("remind_at")
                if due_time and due_time <= now_str:
                    # Fire
                    try:
                        callback(r["task"])
                    except Exception:
                        pass  # never crash the checker

                    # Reschedule if repeating
                    moved = _advance_reminder(r)
                    if moved:
                        remaining.append(moved)
                        changed = True
                else:
                    remaining.append(r)

            if changed or len(remaining) != len(reminders):
                save_reminders(remaining)

            time.sleep(1)

    t = threading.Thread(target=run, daemon=True)
    t.start()
