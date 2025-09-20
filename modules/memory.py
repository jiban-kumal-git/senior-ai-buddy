import json
import os

PROFILE_PATH = os.path.join("data", "user_profile.json")

# Keep your original keys
DEFAULT_PROFILE = {
    "user_name": None,
    "favorite_drink": None,
    "favorite_food": None
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
