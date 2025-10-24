# --- Senior AI Buddy: Day 7–18 (TTS + Reminders + STT + PTT + Memory + Emotions + Notes + Contacts/Notify) ---

import re

from modules.memory import (
    load_profile, save_profile,
    get_name, set_name,
    get_drink, set_drink,
    get_food, set_food,
    reset_profile,
    get_voice_enabled, set_voice_enabled,
    get_voice_rate, set_voice_rate,
    # Day 17
    get_notes, add_note, clear_notes,
    # Day 18
    get_contacts, add_contact, remove_contact_like, find_contact,
    clear_contacts 
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
    transcribe_online, transcribe_offline, has_offline_model,
    list_input_devices, set_input_device, mic_test
)

# Day 18 notifications
from modules.notify import send_message, channel_available, get_config

# ---- Global flags / memory ----
ptt_enabled = False
conversation_history = []   # (who, text), last 20 entries


# ========= Helpers =========

def remember(who: str, text: str):
    """Append to conversation log and trim length."""
    global conversation_history
    if text is None:
        return
    conversation_history.append((who, text))
    if len(conversation_history) > 20:
        conversation_history = conversation_history[-20:]


def say(profile, text):
    """Print + speak if voice is enabled and engine available, and remember."""
    print("Buddy:", text)
    remember("Buddy", text)
    if get_voice_enabled(profile) and is_available():
        speak(text, rate=get_voice_rate(profile))


def greet(profile):
    name = get_name(profile)
    if name:
        hello = f" Hi {name}! I'm Senior AI Buddy. Type 'help' for options. (type 'quit' to exit)\n"
    else:
        hello = " Hi! I'm Senior AI Buddy. I don't know your name yet."
    print(hello)
    remember("Buddy", hello)
    if get_voice_enabled(profile) and is_available():
        speak(hello, rate=get_voice_rate(profile))

    if not name:
        name_input = input("What should I call you? ")
        remember("You", name_input)
        if name_input.strip():
            set_name(profile, name_input)
            say(profile, f"Nice to meet you, {get_name(profile)}! I'll remember that.")
        else:
            say(profile, "No worries, we can set your name later. Type: My name is <YourName>")


def detect_emotion(text: str) -> str:
    low = text.lower()
    if any(w in low for w in ["tired", "sleepy", "exhausted", "fatigued"]):
        return "tired"
    if any(w in low for w in ["sad", "upset", "lonely", "depressed"]):
        return "sad"
    if any(w in low for w in ["happy", "excited", "great", "good mood", "joy"]):
        return "happy"
    if any(w in low for w in ["angry", "mad", "frustrated", "annoyed"]):
        return "angry"
    return ""


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

  Notes:
    - note that <text>
    - my notes / show notes / list notes
    - clear notes
    - clear chat memory     (clears short-term conversation history)

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
    - voice on / voice off
    - set voice rate 150          (range ~100-250)
    - list voices
    - set voice aria              (or jenny/sara/...)
    - speak <anything>
    - speak direct <anything>     (blocking test)
    - beep

  Speech-to-Text:
    - listen-online 5             (record N seconds & transcribe online)

  Push-to-Talk:
    - ptt on                      (then press Enter empty to talk 5s)
    - ptt off

  Microphone:
    - audio devices               (list input devices)
    - set input device <index>    (pick your mic)
    - mic test 3                  (records 3s to mic_test.wav)

  Contacts & Notify:
    - add contact <Name> [phone <num>] [email <addr>] [relation <rel>]
    - list contacts
    - remove contact <Name>
    - notify <Name> <message>
    - emergency <message> to <Name>
    - test notify <channel>       (console | email | sms | whatsapp)

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


def parse_add_contact_cmd(text: str):
    """
    Parse: add contact <Name> [phone <num>] [email <addr>] [relation <rel>]
    Allows spaces in relation; email is one token; phone spaces are stripped.
    """
    m = re.match(
        r"add\s+contact\s+(?P<name>.+?)(?:\s+phone\s+(?P<phone>.+?))?(?:\s+email\s+(?P<email>\S+))?(?:\s+relation\s+(?P<relation>.+))?$",
        text.strip(),
        flags=re.IGNORECASE,
    )
    if not m:
        return None, None, None, None
    name = (m.group("name") or "").strip()
    phone = (m.group("phone") or "").strip()
    email = (m.group("email") or "").strip()
    relation = (m.group("relation") or "").strip()
    if phone:
        phone = phone.replace(" ", "")
    if not email:
        email = None
    if not relation:
        relation = None
    if not name:
        return None, None, None, None
    return name, (phone or None), email, relation


# ========= Core text handler =========

def handle_text(profile, text: str):
    global ptt_enabled

    t = text.strip()
    low = t.lower()

    # ---- Push-to-Talk toggle ----
    if low == "ptt on":
        ptt_enabled = True
        return None, "Push-to-talk mode ENABLED. Just press Enter to speak."
    if low == "ptt off":
        ptt_enabled = False
        return None, "Push-to-talk mode DISABLED."

    # ---- Microphone helpers ----
    if low == "audio devices":
        devs = list_input_devices()
        if not devs:
            return None, "No input devices found."
        out = ["Input devices:"]
        for idx, name in devs:
            out.append(f"  {idx}: {name}")
        return None, "\n".join(out)

    if low.startswith("set input device"):
        parts = t.split()
        if len(parts) >= 4:
            try:
                idx = int(parts[3])
            except Exception:
                return None, "Please give a device index number. Try: audio devices"
            ok = set_input_device(idx)
            return None, ("Mic input device set." if ok else "Invalid device index. Try: audio devices")
        else:
            return None, "Usage: set input device <index>"

    if low.startswith("mic test"):
        parts = t.split()
        secs = 3
        if len(parts) >= 3:
            try:
                secs = max(2, min(10, int(parts[2])))
            except Exception:
                pass
        path = mic_test(seconds=secs)
        return None, f"Mic test saved: {path}. Play it to check your voice level."

    # ---- Speech-to-Text (online) ----
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
        remember("You", said)
        action2, msg2 = handle_text(profile, said)
        if action2 == "quit":
            return None, msg2
        return None, msg2

    # ---- System ----
    if low == "quit":
        return "quit", "Goodbye for now! Stay safe."
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

    # ---- Voice controls ----
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
        voices = list_voices()  # Edge TTS voices
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
    if low.startswith("speak direct "):
        msg = text[len("speak direct "):].strip()
        if msg:
            ok = speak_blocking(msg, rate=get_voice_rate(profile))
            return None, "(direct spoke via worker)" if ok else "Direct speak (worker) timed out."
        else:
            return None, "What should I speak directly?"
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

    # ---- Day 17: Notes ----
    if low.startswith("note that "):
        content = text[len("note that "):].strip()
        if not content:
            return None, "What should I note?"
        ok = add_note(profile, content)
        return None, ("Noted. 📘" if ok else "Couldn't save that note.")
    if low in ("my notes", "show notes", "list notes"):
        notes = get_notes(profile)
        if not notes:
            return None, "You have no notes yet."
        lines = ["Your notes:"]
        for i, n in enumerate(notes, start=1):
            lines.append(f"  {i}. {n['text']}  ({n['added_at']})")
        return None, "\n".join(lines)
    if low == "clear notes":
        clear_notes(profile)
        return None, "All notes cleared."
    if low == "clear chat memory":
        global conversation_history
        conversation_history = []
        return None, "Chat memory cleared."

    # ---- Day 18: Contacts ----
    if low.startswith("add contact "):
        name, phone, email, relation = parse_add_contact_cmd(t)
        if not name:
            return None, "Usage: add contact <Name> [phone <num>] [email <addr>] [relation <rel>]"
        ok = add_contact(profile, name=name, phone=phone, email=email, relation=relation)
        return None, ("Contact saved." if ok else "Couldn't save contact.")

    if low == "list contacts":
        cs = get_contacts(profile)
        if not cs:
            return None, "No contacts yet. Add one with: add contact Mom phone +614... email mom@... relation mother"
        lines = ["Your contacts:"]
        for i, c in enumerate(cs, start=1):
            name = c.get("name", "—")
            phone = c.get("phone", "—")
            email = c.get("email", "—")
            relation = c.get("relation", "—")
            lines.append(f"  {i}. {name}  phone={phone}  email={email}  relation={relation}")
        return None, "\n".join(lines)

    if low.startswith("remove contact like "):
        pat = t[len("remove contact like "):].strip()
        ok = remove_contact_like(profile, pat)
        return None, ("Removed any matching contacts." if ok else "No matching contact.")

    if low == "clear contacts":
        ok = clear_contacts(profile)
        return None, ("All contacts cleared." if ok else "Couldn't clear contacts.")

    # ---- Day 18: Notifications ----
    # notify <Name> <message>
    if low.startswith("notify "):
        rest = text[len("notify "):].strip()
        parts = rest.split(" ", 1)
        if len(parts) < 2:
            return None, "Usage: notify <Name> <message>"
        who, msg = parts[0].strip(), parts[1].strip()
        c = find_contact(profile, who)
        if not c:
            return None, f"I don't see a contact named {who}. Add one with: add contact {who} phone <num> email <addr>"
        cfg = get_config()
        ch = cfg.get("DEFAULT_CHANNEL", "console").lower()
        target = None
        if ch == "email" and c.get("email"):
            target = c["email"]
        elif ch == "sms" and c.get("phone"):
            target = c["phone"]
        elif ch == "whatsapp" and c.get("phone"):
            target = c["phone"]
        else:
            # fallback: email > sms > whatsapp > console
            if c.get("email") and channel_available("email"):
                ch, target = "email", c["email"]
            elif c.get("phone") and channel_available("sms"):
                ch, target = "sms", c["phone"]
            elif c.get("phone") and channel_available("whatsapp"):
                ch, target = "whatsapp", c["phone"]
            else:
                ch, target = "console", c.get("name") or who
        ok = send_message(ch, target, msg)
        return None, (f"Notified {who} via {ch}." if ok else f"Failed to notify {who} via {ch}.")

    # emergency <message> to <Name>
    if low.startswith("emergency "):
        rest = text[len("emergency "):].strip()
        if " to " not in rest.lower():
            return None, "Usage: emergency <message> to <Name>"
        msg_part, who_part = rest.split(" to ", 1)
        who = who_part.strip()
        msg = f"EMERGENCY: {msg_part.strip()}"
        c = find_contact(profile, who)
        if not c:
            return None, f"I don't see a contact named {who}."
        # prefer SMS for emergency, then WhatsApp, then email, then console
        if c.get("phone") and channel_available("sms"):
            ok = send_message("sms", c["phone"], msg)
            return None, ("Emergency SMS sent." if ok else "Failed to send emergency SMS.")
        if c.get("phone") and channel_available("whatsapp"):
            ok = send_message("whatsapp", c["phone"], msg)
            return None, ("Emergency WhatsApp sent." if ok else "Failed to send emergency WhatsApp.")
        if c.get("email") and channel_available("email"):
            ok = send_message("email", c["email"], msg, subject="EMERGENCY")
            return None, ("Emergency email sent." if ok else "Failed to send emergency email.")
        ok = send_message("console", who, msg)
        return None, ("Emergency console notify shown." if ok else "Couldn't notify.")

    # test notify <channel>
    if low.startswith("test notify "):
        ch = t[len("test notify "):].strip().lower()
        if ch not in ("console", "email", "sms", "whatsapp"):
            return None, "Channel must be console, email, sms, or whatsapp."
        target = "Console" if ch == "console" else ("demo@example.com" if ch == "email" else "+10000000000")
        ok = send_message(ch, target, "Test message from Senior AI Buddy.")
        return None, ("Test sent." if ok else "Test failed.")

    # ---- Reminders ----
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

    if low.startswith("remind me to"):
        task = t[11:].strip()
        if task:
            add_text_reminder(task)
            return None, f"Okay, I'll remind you to: {task} (saved)."
        else:
            return None, "Remind you to… what? Please say the task."

    if low == "show reminders":
        return None, render_reminders()
    if low == "clear reminders":
        clear_reminders()
        return None, "All reminders cleared."

    # ---- Small talk ----
    if "hello" in low:
        name = get_name(profile)
        return None, (f"Hello, {name}! How's your day going?" if name else "Hello there! How's your day going?")
    if "namaste" in low:
        name = get_name(profile)
        return None, (f"Namaste, {name}! I'm happy to chat with you." if name else "Namaste!I'm happy to chat with you.")
    if "tea" in low:
        return None, "Ah, tea is always a good choice."
    if "coffee" in low:
        return None, "Coffee will keep you energized!"

    # ---- Emotion-aware replies (Day 16) ----
    mood = detect_emotion(t)
    if mood == "tired":
        return None, "You sound tired. Maybe a little rest or tea would help."
    if mood == "sad":
        return None, "I'm sorry you're feeling down. Remember, you're not alone — I'm here with you."
    if mood == "happy":
        return None, "Yay! I'm glad to hear you're happy. Let's celebrate that energy!"
    if mood == "angry":
        return None, "It sounds like you're upset. Want to talk about what's bothering you?"

    # ---- Default fallback with conversation memory ----
    name = get_name(profile)
    if name and conversation_history:
        last_user_msgs = [m for m in conversation_history if m[0] == "You"]
        if last_user_msgs:
            recent = last_user_msgs[-1][1]
            return None, f"I hear you, {name}. Earlier you said: '{recent}'. Do you want to talk more about that?"

    return None, "Hmm, I don't fully understand yet, but I'm listening."


# ========= Program starts here =========
print("Loading your profile...")
profile = load_profile()

# Start TTS worker early so greetings + reminders can speak (hint a nice neural voice)
if is_available():
    start_worker(default_rate=get_voice_rate(profile), voice_hint="sara")

# Reminder callback
def on_reminder(task):
    msg = f"⏰ Reminder: {task}"
    print(f"\n{msg}")
    beep()
    if get_voice_enabled(profile) and is_available():
        speak("Reminder! " + task, rate=get_voice_rate(profile))
    print("You: ", end="", flush=True)

# Kick off background reminder checker
reminder_checker(on_reminder)

greet(profile)

while True:
    try:
        user_input = input("You: ")
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
        break

    # Push-to-talk: Enter on empty line → listen 5s
    if ptt_enabled and user_input.strip() == "":
        print("(PTT listening 5s...)")
        said = transcribe_online(seconds=5)
        if said:
            print(f"You (voice): {said}")
            remember("You", said)
            action, message = handle_text(profile, said)
        else:
            action, message = None, "I didn’t catch that."
    else:
        remember("You", user_input)
        action, message = handle_text(profile, user_input)

    if action == "quit":
        say(profile, message)
        break
    if message:
        say(profile, message)
