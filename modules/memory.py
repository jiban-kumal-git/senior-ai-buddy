import json
import os

PROFILE_PATH = os.path.join("data", "user_profile.json")

# Keep your original keys
DEFAULT_PROFILE = {
    "user_name": None,
    "favorite_drink": None,
    "favorite_food": None,
    "notes": [],
    "contacts": []
}


def load_profile():
    """Load user profile from JSON; create with defaults if missing/corrupt.
       Also migrates old 'name' -> 'user_name' if present."""
    if not os.path.exists(PROFILE_PATH):
        save_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE.copy()

    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ensure all expected keys exist
        for k, v in DEFAULT_PROFILE.items():
            data.setdefault(k, v)

        # ---- Migration: if older files had "name", move it to "user_name"
        if data.get("user_name") is None and isinstance(data.get("name"), str):
            data["user_name"] = data["name"]
            try:
                del data["name"]
            except KeyError:
                pass
            save_profile(data)
        # ---- end migration

        return data
    except Exception:
        # If file is broken, start fresh (don’t crash)
        save_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE.copy()

def save_profile(profile):
    """Save user profile to JSON file."""
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

# ---------- Helper functions (module-level; importable) ----------

def get_name(profile):
    return profile.get("user_name")

def set_name(profile, name: str):
    profile["user_name"] = name.strip().title() if name else None
    save_profile(profile)

def get_drink(profile):
    return profile.get("favorite_drink")

def set_drink(profile, drink: str):
    profile["favorite_drink"] = drink.strip() if drink else None
    save_profile(profile)

def get_food(profile):
    return profile.get("favorite_food")

def set_food(profile, food: str):
    profile["favorite_food"] = food.strip() if food else None
    save_profile(profile)

def reset_profile():
    """Clear everything back to defaults and save."""
    fresh = DEFAULT_PROFILE.copy()
    save_profile(fresh)
    return fresh

def get_voice_enabled(profile):
    v = profile.get("voice_enabled")
    if v is None:
        profile["voice_enabled"] = True
        save_profile(profile)
        return True
    return bool(v)

def set_voice_enabled(profile, enabled: bool):
    profile["voice_enabled"] = bool(enabled)
    save_profile(profile)

def get_voice_rate(profile):
    r = profile.get("voice_rate")
    if not isinstance(r, int):
        profile["voice_rate"] = 170
        save_profile(profile)
        return 170
    return r

def set_voice_rate(profile, rate: int):
    try:
        r = int(rate)
    except Exception:
        r = 170
    profile["voice_rate"] = max(100, min(250, r))  # clamp: 100–250
    save_profile(profile)

from datetime import datetime

def get_notes(profile):
    # Always return a list
    notes = profile.get("notes")
    if not isinstance(notes, list):
        notes = []
        profile["notes"] = notes
        save_profile(profile)
    return notes

def add_note(profile, text: str):
    text = (text or "").strip()
    if not text:
        return False
    # store timestamped note; simple dict to allow future expansion
    note = {
        "text": text,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    notes = get_notes(profile)
    notes.append(note)
    save_profile(profile)
    return True

def clear_notes(profile):
    profile["notes"] = []
    save_profile(profile)
    return True

def get_contacts(profile):
    contacts = profile.get("contacts")
    if not isinstance(contacts, list):
        contacts = []
        profile["contacts"] = contacts
        save_profile(profile)
    return contacts

def add_contact(profile, name: str, phone: str | None = None, email: str | None = None, relation: str | None = None):
    name = (name or "").strip()
    if not name:
        return False
    contacts = get_contacts(profile)
    # replace if same name exists
    for c in contacts:
        if c.get("name","").lower() == name.lower():
            c.update({"phone": phone, "email": email, "relation": relation})
            save_profile(profile)
            return True
    contacts.append({"name": name, "phone": phone, "email": email, "relation": relation})
    save_profile(profile)
    return True

def remove_contact_like(profile, pattern: str):
    pat = (pattern or "").strip().lower()
    if not pat:
        return False
    contacts = get_contacts(profile)
    new_list = [c for c in contacts if pat not in str(c.get("name","")).lower()]
    if len(new_list) == len(contacts):
        return False
    profile["contacts"] = new_list
    save_profile(profile)
    return True

def find_contact(profile, name: str):
    name = (name or "").strip()
    for c in get_contacts(profile):
        if c.get("name","").lower() == name.lower():
            return c
    return None

def clear_contacts(profile):
    profile["contacts"] = []
    save_profile(profile)
    return True


