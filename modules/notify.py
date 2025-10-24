# modules/notify.py
import os
import smtplib
from email.mime.text import MIMEText
from typing import Optional, Dict
from dotenv import load_dotenv

# Optional Twilio; guard import
try:
    from twilio.rest import Client as TwilioClient
    _twilio_ok = True
except Exception:
    _twilio_ok = False

load_dotenv()  # load .env if present

# ---------------------------
# Config helpers
# ---------------------------
def get_config() -> Dict[str, Optional[str]]:
    return {
        "EMAIL_HOST": os.getenv("EMAIL_HOST"),            # e.g., smtp.gmail.com
        "EMAIL_PORT": os.getenv("EMAIL_PORT"),            # e.g., 587
        "EMAIL_USER": os.getenv("EMAIL_USER"),
        "EMAIL_PASS": os.getenv("EMAIL_PASS"),            # app password recommended
        "TWILIO_SID": os.getenv("TWILIO_SID"),
        "TWILIO_AUTH": os.getenv("TWILIO_AUTH"),
        "TWILIO_FROM": os.getenv("TWILIO_FROM"),          # e.g., +12025551234 or whatsapp:+12025551234
        "DEFAULT_CHANNEL": os.getenv("DEFAULT_CHANNEL", "console"), # console | email | sms | whatsapp
    }

def channel_available(channel: str) -> bool:
    cfg = get_config()
    if channel == "console":
        return True
    if channel == "email":
        return all([cfg["EMAIL_HOST"], cfg["EMAIL_PORT"], cfg["EMAIL_USER"], cfg["EMAIL_PASS"]])
    if channel in ("sms", "whatsapp"):
        return _twilio_ok and all([cfg["TWILIO_SID"], cfg["TWILIO_AUTH"], cfg["TWILIO_FROM"]])
    return False

# ---------------------------
# Senders
# ---------------------------
def send_console(to: str, message: str) -> bool:
    print(f"[NOTIFY console] -> {to}: {message}")
    return True

def send_email(to_email: str, message: str, subject: str = "Senior AI Buddy Notification") -> bool:
    cfg = get_config()
    if not channel_available("email"):
        print("[notify] Email not configured; falling back to console.")
        return send_console(to_email, message)

    try:
        port = int(cfg["EMAIL_PORT"])
        msg = MIMEText(message, "plain", "utf-8")
        msg["From"] = cfg["EMAIL_USER"]
        msg["To"] = to_email
        msg["Subject"] = subject

        with smtplib.SMTP(cfg["EMAIL_HOST"], port) as server:
            server.starttls()
            server.login(cfg["EMAIL_USER"], cfg["EMAIL_PASS"])
            server.send_message(msg)
        print(f"[NOTIFY email] sent to {to_email}")
        return True
    except Exception as e:
        print(f"[notify] Email send failed: {e}")
        return False

def _twilio_client():
    cfg = get_config()
    return TwilioClient(cfg["TWILIO_SID"], cfg["TWILIO_AUTH"])

def send_sms(to_number: str, message: str) -> bool:
    cfg = get_config()
    if not channel_available("sms"):
        print("[notify] SMS not configured; falling back to console.")
        return send_console(to_number, message)
    try:
        client = _twilio_client()
        client.messages.create(
            body=message,
            from_=cfg["TWILIO_FROM"],
            to=to_number
        )
        print(f"[NOTIFY sms] sent to {to_number}")
        return True
    except Exception as e:
        print(f"[notify] SMS send failed: {e}")
        return False

def send_whatsapp(to_number: str, message: str) -> bool:
    cfg = get_config()
    if not channel_available("whatsapp"):
        print("[notify] WhatsApp not configured; falling back to console.")
        return send_console(to_number, message)
    try:
        client = _twilio_client()
        # Twilio requires prefix 'whatsapp:' for WhatsApp
        from_num = cfg["TWILIO_FROM"]
        if not str(from_num).startswith("whatsapp:"):
            from_num = f"whatsapp:{from_num}"
        to_num = to_number if str(to_number).startswith("whatsapp:") else f"whatsapp:{to_number}"
        client.messages.create(
            body=message,
            from_=from_num,
            to=to_num
        )
        print(f"[NOTIFY whatsapp] sent to {to_number}")
        return True
    except Exception as e:
        print(f"[notify] WhatsApp send failed: {e}")
        return False

# ---------------------------
# Facade
# ---------------------------
def send_message(channel: str, to: str, message: str, subject: Optional[str] = None) -> bool:
    """
    channel: console | email | sms | whatsapp
    """
    ch = channel.strip().lower()
    if ch == "email":
        return send_email(to, message, subject or "Senior AI Buddy")
    if ch == "sms":
        return send_sms(to, message)
    if ch == "whatsapp":
        return send_whatsapp(to, message)
    # default
    return send_console(to, message)
