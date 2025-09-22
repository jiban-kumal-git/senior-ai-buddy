# --- Day 10: Clock-time reminders (8:30 pm / 7 am / 19:30) ---

from modules.memory import (
    load_profile, save_profile,
    get_name, set_name,
    get_drink, set_drink,
    get_food, set_food,
    reset_profile
)
from modules.reminders import (
    add_text_reminder, add_timed_reminder, add_clock_reminder,
    load_reminders, clear_reminders, reminder_checker
)

def greet(profile):
    name = get_name(profile)
    if name:
        print(f"👋 Hi {name}! I’m Senior AI Buddy. Type 'help' for options. (type 'quit' to exit)\n")
    else:
        print("👋 Hi! I’m Senior AI Buddy. I don’t know your name yet.")
        name_input = input("What should I call you? ")
        if name_input.strip():
            set_name(profile, name_input)
            print(f"Nice to meet you, {get_name(profile)}! I’ll remember that. 😊")
        else:
            print("No worries, we can set your name later. Type: My name is <YourName>")

def show_help():
    print("""
Commands you can try:
  Profile & Memory:
    - My name is <YourName>
    - I like <drink>
    - My favorite food is <food>
    - What's my name / drink / food
    - profile
    - reset my profile

  Reminders (basic):
    - remind me to <task>
    - show reminders
    - clear reminders

  Timed reminders (Day 9):
    - remind me in 10 seconds to <task>
    - remind me in 2 minutes to <task>

  Clock-time reminders (Day 10):
    - remind me at 8:30 pm to <task>
    - remind me at 7 am to <task>
    - remind me at 19:45 to <task>

  Other:
    - hello / namaste / tea / coffee
    - help
    - quit
""")

def show_profile(profile):
    print("—— Your Saved Profile ——")
    print(f"Name:           {get_name(profile) or '—'}")
    print(f"Favorite drink: {get_drink(profile) or '—'}")
    print(f"Favorite food:  {get_food(profile) or '—'}")
    print("-------------------------")

def render_reminders():
    items = load_reminders()
    if not items:
        return "You don’t have any reminders yet."
    lines = ["Here are your reminders:"]
    for i, r in enumerate(items, start=1):
        task = r.get("task", "")
        when = r.get("remind_at")
        if when:
            lines.append(f"  {i}. {task}  (at {when})")
        else:
            lines.append(f"  {i}. {task}")
    return "\n".join(lines)

def handle_text(profile, text: str):
    t = text.strip()
    low = t.lower()

    # Exit
    if low == "quit":
        return "quit", "Goodbye for now! 👋 Stay safe."

    # Help & profile
    if low == "help":
        show_help()
        return None, None
    if low == "profile":
        show_profile(profile)
        return None, None
    if low == "reset my profile":
        newp = reset_profile()
        profile.clear(); profile.update(newp)
        return None, "Okay, I reset your profile to defaults."

    # Setters
    if low.startswith("my name is"):
        set_name(profile, t[10:].strip())
        return None, f"Nice to meet you, {get_name(profile)}! I’ll remember your name. 😊"

    if low.startswith("i like"):
        set_drink(profile, t[6:].strip())
        return None, f"Cool! I’ll remember you like {get_drink(profile)}."

    if low.startswith("my favorite food is"):
        set_food(profile, t[20:].strip())
        return None, f"Got it! Favorite food: {get_food(profile)}. Saved. 🍽️"

    if low.startswith("i eat"):
        set_food(profile, t[5:].strip())
        return None, f"Yum! I’ll remember you eat {get_food(profile)}."

    # Queries
    if "what's my name" in low or "whats my name" in low:
        name = get_name(profile)
        return None, (f"Your name is {name}, of course! 😉" if name else "Hmm, I don’t know your name yet.")
    if "what's my drink" in low or "whats my drink" in low:
        drink = get_drink(profile)
        return None, (f"You like {drink}, don’t you? ☕" if drink else "You haven’t told me your favorite drink yet.")
    if "what's my food" in low or "whats my food" in low:
        food = get_food(profile)
        return None, (f"Your favorite food is {food}." if food else "You haven’t told me your favorite food yet.")

    # ---------------- Reminders (Day 8/9/10) ----------------

    # Day 10: Clock-time -> "remind me at <time> to <task>"
    if low.startswith("remind me at"):
        # Split only the first 4 chunks so the rest stays as "<time> to <task>"
        parts = t.split(" ", 3)  # ["remind","me","at","<time> to <task>"]
        if len(parts) < 4:
            return None, "Try: remind me at 8:30 pm to take medicine"
        remainder = parts[3].strip()  # "<time> to <task>"
        if " to " not in remainder.lower():
            return None, "Use 'to' before the task. Example: remind me at 7 am to drink water"
        time_part, task_part = remainder.split(" to ", 1)
        time_str = time_part.strip()
        task = task_part.strip()
        if not task:
            return None, "Remind you to… what? Please say the task."
        try:
            remind_at = add_clock_reminder(task, time_str)
            return None, f"Okay! I’ll remind you at {remind_at} to: {task}"
        except Exception:
            return None, "I couldn’t read that time. Try formats like '8:30 pm', '7 am', or '19:45'."

    # Day 9: Timed -> "remind me in <N> seconds/minutes to <task>"
    if low.startswith("remind me in"):
        parts = t.split(" ", 4)  # ["remind","me","in","10","seconds to <task>"]
        if len(parts) < 5:
            return None, "Try: remind me in 10 seconds to drink water"
        number_str = parts[3].strip()
        rest = parts[4]
        try:
            number = int(number_str)
        except ValueError:
            return None, "Please give a number, e.g., 10 seconds or 2 minutes."
        rest_low = rest.lower()
        if "second" in rest_low:
            task = rest_low.replace("seconds", "").replace("second", "").replace("to", "", 1).strip()
            if not task:
                return None, "Remind you to… what? Please say the task."
            remind_at = add_timed_reminder(task, number)
            return None, f"Okay! I’ll remind you at {remind_at} to: {task}"
        elif "minute" in rest_low:
            task = rest_low.replace("minutes", "").replace("minute", "").replace("to", "", 1).strip()
            if not task:
                return None, "Remind you to… what? Please say the task."
            remind_at = add_timed_reminder(task, number * 60)
            return None, f"Okay! I’ll remind you at {remind_at} to: {task}"
        else:
            return None, "Please specify seconds or minutes. Example: remind me in 2 minutes to drink water"

    # Day 8: Simple text reminder -> "remind me to <task>"
    if low.startswith("remind me to"):
        task = t[11:].strip()
        if task:
            add_text_reminder(task)
            return None, f"Okay, I’ll remind you to: {task} (saved)."
        else:
            return None, "Remind you to… what? Please say the task."

    # Show/Clear
    if low == "show reminders":
        return None, render_reminders()
    if low == "clear reminders":
        clear_reminders()
        return None, "All reminders cleared."

    # ---------------- Small talk ----------------
    if "hello" in low:
        name = get_name(profile)
        return None, (f"Hello, {name}! How’s your day going?" if name else "Hello there! How’s your day going?")
    if "namaste" in low:
        name = get_name(profile)
        return None, (f"Namaste, {name}! 🙏 I’m happy to chat with you." if name else "Namaste 🙏 I’m happy to chat with you.")
    if "tea" in low:
        return None, "Ah, tea ☕ is always a good choice."
    if "coffee" in low:
        return None, "Coffee ☕ will keep you energized!"

    # Default fallback
    name = get_name(profile)
    if name:
        return None, f"I hear you, {name}. Tell me more!"
    return None, "Hmm, I don’t fully understand yet, but I’m learning! 🤓"


# ---------- Program starts here ----------
print("Loading your profile...")
profile = load_profile()

# Background checker prints reminders when due
def on_reminder(task):
    print(f"\n⏰ Reminder: {task}\nYou: ", end="", flush=True)

reminder_checker(on_reminder)

greet(profile)

while True:
    user_input = input("You: ")
    action, message = handle_text(profile, user_input)
    if action == "quit":
        print("Buddy:", message)
        break
    if message:
        print("Buddy:", message)
