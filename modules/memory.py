import json
import os

PROFILE_PATH = os.path.join("data", "user_profile.json")

DEFAULT_PROFILE = {
    "user_name": None,
    "favorite_drink": None,
    "favorite_food": None
}

def load_profile():
    # Load user profile from a JSON file; create with defaults if missing/corrupt.
    if not os.path.exists(PROFILE_PATH):
        save_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE.copy()
    
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Make sure all expected keys exist (in case file is old)
            for k, v in DEFAULT_PROFILE.items():
                data.setdefault(k, v)
            return data
    except Exception:
        # If file is broken, start fresh (don't crash)
        save_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE.copy()
    
def save_profile(profile):
    # Save user profile to JSON file.
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)