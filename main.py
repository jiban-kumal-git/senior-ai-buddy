# --- Day 12 (+ Day 7–14 features) with robust TTS worker, STT, and Push-to-Talk ---

from modules.memory import (
    load_profile, save_profile,
    get_name, set_name,
    get_drink, set_drink,
    get_food, set_food,
    reset_profile,
    get_voice_enabled, set_voice_enabled,
    get_voice_rate, set_voice_rate
)

from modules.reminders import (
    add_text_reminder, add_timed_reminder, add_clock_reminder,
    add_daily_reminder, add_weekly_reminder,
    load_reminders, clear_reminders, reminder_checker
)

from modules.voice import (
    speak, speak_blocking, is_available, start_worker,
    list_voices, set_voice_by_name, beep
)

from modules.stt import (
    transcribe_offline, transcribe_online, has_offline_model
)

# ---- Global flags ----
ptt_enabled = False


def say(profile, text):
    """Print + speak if voice is enabled and engine available."""
    print("Buddy:", text)
    if get_voice_enabled(profile) and is_available():
        speak(text, rate=get_voice_rate(profile))


def greet(profile):
    name = get_name(profile)
    if name:
        hello = f"👋 Hi {name}! I'm Senior AI Buddy. Type 'help' for options. (type 'quit' to exit)\n"
    else:
        hello = "👋 Hi! I'm Senior AI Buddy. I don't know your name yet."
    print(hello)
    if get_voice_enabled(profile) and is_available():
        speak(hello, rate=get_voice_rate(profile))

    if not name:
        name_input = input("What should I call you? ")
        if name_input.strip():
            set_name(profile, name_input)
            say(profile, f"Nice to meet you, {get_name(profile)}! I'll remember that. 😊")
        else:
            say(profile, "No worries, we can set your name later. Type: My name is <YourName>")


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

  Reminders:
    - remind me to <task>
    - remind me in 10 seconds to <task>
    - remind me in 2 minutes to <task>
    - remind me at 8:30 pm to <task>
    - remind me every day at 8 am to <task>
    - remind me every monday at 7 pm to <task>
    - show reminders
    - clear reminders

  Voice:
    - voice on
    - voice off
    - set voice rate 150          (range ~100-250)
    - list voices
    - set voice aria              (or zira/jenny/sara, etc.)
    - speak <anything>
    - beep

  Speech-to-Text:
    - listen-online 5             (record N seconds & transcribe)

  Push-to-Talk:
    - ptt on                      (then press Enter with empty input to talk 5s)
    - ptt off

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
    print(f"Voice enabled:  {get_voice_enabled(profile)}")
    print(f"Voice rate:     {get_voice_rate(profile)}")
    print("-------------------------")


def render_reminders():
    items = load_reminders()
    if not items:
        return "You don't have any reminders yet."
    lines = ["Here are your reminders:"]
    for i, r in enumerate(items, start=1):
        task = r.get("task", "")
        when = r.get("remind_at")
        repeat = r.get("repeat")
        if repeat:
            lines.append(f"  {i}. {task}  (at {when}, repeat={repeat})")
        elif when:
            lines.append(f"  {i}. {task}  (at {when})")
        else:
            lines.append(f"  {i}. {task}")
    return "\n".join(lines)


def handle_text(profile, text: str):
    global ptt_enabled

    # Always keep these first!
    t = text.strip()
    low = t.lower()

    # ---- Push-to-Talk (Day 14) ----
    if low == "ptt on":
        ptt_enabled = True
        return None, "Push-to-talk mode ENABLED. Just press Enter to speak."
    if low == "ptt off":
        ptt_enabled = False
        return None, "Push-to-talk mode DISABLED."

    # ---- Speech-to-Text (Day 13): ONLINE ----
    if low.startswith("listen-online"):
        parts = t.split()
        secs = 5
        if len(parts) >= 2:
            try:
                secs = max(2, min(30, int(parts[1])))
            except Exception:
                pass

        print(f"(listening online for {secs}s...)")
        said = transcribe_online(seconds=secs)
        if not said:
            return None, "I didn’t catch that (online). Try again or speak closer to the mic."
        print(f"You (voice): {said}")
        action2, msg2 = handle_text(profile, said)
        if action2 == "quit":
            return None, msg2
        return None, msg2

    # Exit
    if low == "quit":
        return "quit", "Goodbye for now! Stay safe."

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

    # ---------------- Voice controls ----------------
    if low == "voice on":
        set_voice_enabled(profile, True)
        return None, "Voice turned ON."

    if low == "voice off":
        set_voice_enabled(profile, False)
        return None, "Voice turned OFF."

    if low.startswith("set voice rate"):
        parts = low.split()
        try:
            rate = int(parts[-1])
            set_voice_rate(profile, rate)
            return None, f"Voice rate set to {get_voice_rate(profile)}."
        except Exception:
            return None, "Please provide a number, e.g., set voice rate 170"

    if low == "list voices":
        voices = list_voices()  # Edge TTS: list of (ShortName, Locale, Gender)
        if not voices:
            return None, "No voices available."
        msg = ["Available voices:"]
        for i, (short, locale, gender) in enumerate(voices, start=1):
            msg.append(f"  {i}. {short}  [{locale}, {gender}]")
        return None, "\n".join(msg)

    if low.startswith("set voice "):
        target = t[10:].strip()
        if not target:
            return None, "Please provide part of a voice name, e.g., set voice aria"
        ok = set_voice_by_name(target)
        return None, ("Voice set." if ok else "Could not find that voice. Try 'list voices'.")

    if low == "beep":
        beep()
        return None, "(beep)"

    # NEW: direct speech test (blocking via worker)
    if low.startswith("speak direct "):
        msg = text[len("speak direct "):].strip()
        if msg:
            ok = speak_blocking(msg, rate=get_voice_rate(profile))
            return None, "(direct spoke via worker)" if ok else "Direct speak (worker) timed out."
        else:
            return None, "What should I speak directly?"

    # Normal queued speech (uses background TTS worker)
    if low.startswith("speak "):
        msg = t[6:].strip()
        if msg:
            if get_voice_enabled(profile) and is_available():
                speak(msg, rate=get_voice_rate(profile))
                print(f"(speaking) {msg}")
            else:
                return None, "Voice engine not available or voice is OFF."
            return None, None
        else:
            return None, "What should I speak?"

    # ---------------- Memory setters ----------------
    if low.startswith("my name is"):
        set_name(profile, t[10:].strip())
        return None, f"Nice to meet you, {get_name(profile)}! I'll remember your name. 😊"

    if low.startswith("i like"):
        set_drink(profile, t[6:].strip())
        return None, f"Cool! I'll remember you like {get_drink(profile)}."

    if low.startswith("my favorite food is"):
        set_food(profile, t[20:].strip())
        return None, f"Got it! Favorite food: {get_food(profile)}. Saved. 🍽️"

    if low.startswith("i eat"):
        set_food(profile, t[5:].strip())
        return None, f"Yum! I'll remember you eat {get_food(profile)}."

    # ---------------- Memory queries ----------------
    if "what's my name" in low or "whats my name" in low:
        name = get_name(profile)
        return None, (f"Your name is {name}, of course! 😉" if name else "Hmm, I don't know your name yet.")
    if "what's my drink" in low or "whats my drink" in low:
        drink = get_drink(profile)
        return None, (f"You like {drink}, don't you? ☕" if drink else "You haven't told me your favorite drink yet.")
    if "what's my food" in low or "whats my food" in low:
        food = get_food(profile)
        return None, (f"Your favorite food is {food}." if food else "You haven't told me your favorite food yet.")

    # ---------------- Reminders (Day 8/9/10/11) ----------------

    # Recurring daily: "remind me every day at <time> to <task>"
    if low.startswith("remind me every day at"):
        parts = t.split(" ", 5)
        if len(parts) < 6:
            return None, "Try: remind me every day at 8 am to take medicine"
        remainder = parts[5].strip()
        if " to " not in remainder.lower():
            return None, "Use 'to' before the task. Example: remind me every day at 7 am to drink water"
        time_part, task_part = remainder.split(" to ", 1)
        time_str = time_part.strip()
        task = task_part.strip()
        if not task:
            return None, "Remind you to… what? Please say the task."
        try:
            when = add_daily_reminder(task, time_str)
            return None, f"Okay! I'll remind you every day at {when[-8:]} to: {task}"
        except Exception:
            return None, "I couldn't read that time. Try '8:30 pm', '7 am', or '19:45'."

    # Recurring weekly
    if low.startswith("remind me every ") and " at " in low and " to " in low:
        try:
            after_every = t[16:]
            weekday, after_wd = after_every.split(" at ", 1)
            if " to " not in after_wd.lower():
                raise ValueError()
            time_part, task_part = after_wd.split(" to ", 1)
            weekday_name = weekday.strip().lower()
            time_str = time_part.strip()
            task = task_part.strip()
            if not weekday_name or not time_str or not task:
                raise ValueError()
            when = add_weekly_reminder(task, weekday_name, time_str)
            return None, f"Got it! I'll remind you every {weekday_name.capitalize()} at {when[-8:]} to: {task}"
        except Exception:
            pass

    # Clock-time one-off
    if low.startswith("remind me at"):
        parts = t.split(" ", 3)
        if len(parts) < 4:
            return None, "Try: remind me at 8:30 pm to take medicine"
        remainder = parts[3].strip()
        if " to " not in remainder.lower():
            return None, "Use 'to' before the task. Example: remind me at 7 am to drink water"
        time_part, task_part = remainder.split(" to ", 1)
        time_str = time_part.strip()
        task = task_part.strip()
        if not task:
            return None, "Remind you to… what? Please say the task."
        try:
            remind_at = add_clock_reminder(task, time_str)
            return None, f"Okay! I'll remind you at {remind_at} to: {task}"
        except Exception:
            return None, "I couldn't read that time. Try '8:30 pm', '7 am', or '19:45'."

    # Timed relative
    if low.startswith("remind me in"):
        parts = t.split(" ", 4)
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

    # Simple text reminder
    if low.startswith("remind me to"):
        task = t[11:].strip()
        if task:
            add_text_reminder(task)
            return None, f"Okay, I'll remind you to: {task} (saved)."
        else:
            return None, "Remind you to… what? Please say the task."

    # Show/Clear reminders
    if low == "show reminders":
        return None, render_reminders()
    if low == "clear reminders":
        clear_reminders()
        return None, "All reminders cleared."

    # ---------------- Small talk ----------------
    if "hello" in low:
        name = get_name(profile)
        return None, (f"Hello, {name}! How's your day going?" if name else "Hello there! How's your day going?")
    if "namaste" in low:
        name = get_name(profile)
        return None, (f"Namaste, {name}! I'm happy to chat with you." if name else "Namaste 🙏 I'm happy to chat with you.")
    if "tea" in low:
        return None, "Ah, tea is always a good choice."
    if "coffee" in low:
        return None, "Coffee will keep you energized!"

    # Default fallback
    name = get_name(profile)
    if name:
        return None, f"I hear you, {name}. Tell me more!"
    return None, "Hmm, I don't fully understand yet, but I'm learning! 🤓"


# ---------- Program starts here ----------
print("Loading your profile...")
profile = load_profile()

# Start TTS worker early so greetings + reminders can speak
if is_available():
    start_worker(default_rate=get_voice_rate(profile), voice_hint="zira")

# Background checker prints reminders when due (and re-schedules recurring ones)
def on_reminder(task):
    msg = f"⏰ Reminder: {task}"
    print(f"\n{msg}")
    # audible cue
    beep()
    # then TTS via worker
    if get_voice_enabled(profile) and is_available():
        speak("Reminder! " + task, rate=get_voice_rate(profile))
    print("You: ", end="", flush=True)

reminder_checker(on_reminder)

greet(profile)

while True:
    # PTT: if enabled and user just presses Enter → listen 5s
    user_input = input("You: ")
    if ptt_enabled and user_input.strip() == "":
        print("(PTT listening 5s...)")
        said = transcribe_online(seconds=5)
        if said:
            print(f"You (voice): {said}")
            action, message = handle_text(profile, said)
        else:
            action, message = None, "I didn’t catch that."
    else:
        action, message = handle_text(profile, user_input)

    if action == "quit":
        say(profile, message)
        break
    if message:
        say(profile, message)
