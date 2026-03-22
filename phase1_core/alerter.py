# phase1_core/alerter.py
# ─────────────────────────────────────────
#  All Alert Channels – Phase 1
#  Twilio Call · SMS · WhatsApp · Email · Audio
# ─────────────────────────────────────────

import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ══════════════════════════════════════════
#  CHANNEL 1 – Twilio Voice Call
# ══════════════════════════════════════════
def send_twilio_call():
    """
    Makes an automated voice call to ALERT_PHONE_NUMBER.
    Speaks a warning message using Twilio's text-to-speech.
    """
    try:
        from twilio.rest import Client
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        call = client.calls.create(
            twiml='''
                <Response>
                    <Say voice="alice" loop="2">
                        Warning! Warning! The driver appears to be drowsy.
                        Please pull over immediately and take a rest.
                        This is an automated alert from the Driver Drowsy Detection System.
                    </Say>
                </Response>
            ''',
            to=os.getenv("ALERT_PHONE_NUMBER"),
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
        )
        print(f"[✅ CALL] Voice call initiated → SID: {call.sid}")
        return True
    except Exception as e:
        print(f"[❌ CALL] Failed: {e}")
        return False


# ══════════════════════════════════════════
#  CHANNEL 2 – Twilio SMS
# ══════════════════════════════════════════
def send_twilio_sms(message=None):
    """
    Sends an SMS to ALERT_PHONE_NUMBER via Twilio.
    """
    try:
        from twilio.rest import Client
        if not message:
            now     = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            message = (
                f"🚨 DDS ALERT 🚨\n"
                f"Drowsiness detected!\n"
                f"Time: {now}\n"
                f"Please check on the driver immediately."
            )
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        msg = client.messages.create(
            body=message,
            to=os.getenv("ALERT_PHONE_NUMBER"),
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
        )
        print(f"[✅ SMS] Sent → SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"[❌ SMS] Failed: {e}")
        return False


# ══════════════════════════════════════════
#  CHANNEL 3 – WhatsApp via Twilio Sandbox
# ══════════════════════════════════════════
def send_whatsapp_alert(message=None):
    """
    Sends WhatsApp message via Twilio Sandbox.
    Make sure you have joined the sandbox first:
    Twilio Console → Messaging → Try it out → Send a WhatsApp message
    """
    try:
        from twilio.rest import Client
        if not message:
            now     = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            message = (
                f"🚨 *DDS ALERT* 🚨\n\n"
                f"*Drowsiness Detected!*\n"
                f"🕐 Time: {now}\n\n"
                f"Please check on the driver immediately.\n"
                f"_— Driver Drowsy Detection System_"
            )
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        msg = client.messages.create(
            body=message,
            to=os.getenv("WHATSAPP_TO"),
            from_=os.getenv("WHATSAPP_FROM"),
        )
        print(f"[✅ WHATSAPP] Sent → SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"[❌ WHATSAPP] Failed: {e}")
        return False


# ══════════════════════════════════════════
#  CHANNEL 4 – Email via Gmail SMTP
# ══════════════════════════════════════════
def send_email_alert():
    """
    Sends an email alert via Gmail SMTP.
    Use Gmail App Password (not your regular password).
    Generate at: myaccount.google.com → Security → App Passwords
    """
    try:
        sender   = os.getenv("EMAIL_SENDER")
        password = os.getenv("EMAIL_PASSWORD")
        receiver = os.getenv("EMAIL_RECEIVER")
        now      = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Build email
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 DDS Alert – Drowsiness Detected at {now}"
        msg["From"]    = sender
        msg["To"]      = receiver

        # Plain text version
        text = (
            f"DROWSINESS ALERT\n\n"
            f"Time     : {now}\n"
            f"Status   : Drowsiness detected by DDS system\n"
            f"Action   : Please check on the driver immediately!\n\n"
            f"-- Driver Drowsy Detection System"
        )

        # HTML version
        html = f"""
        <html><body>
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;border:2px solid #e53e3e;border-radius:8px;overflow:hidden;">
          <div style="background:#e53e3e;padding:16px;text-align:center;">
            <h2 style="color:white;margin:0;">🚨 DROWSINESS ALERT</h2>
          </div>
          <div style="padding:20px;background:#fff8f8;">
            <p style="font-size:16px;color:#333;"><strong>Time:</strong> {now}</p>
            <p style="font-size:16px;color:#333;"><strong>Status:</strong> Drowsiness detected</p>
            <p style="font-size:16px;color:#e53e3e;"><strong>⚠️ Please check on the driver immediately!</strong></p>
          </div>
          <div style="padding:12px;background:#fff0f0;text-align:center;">
            <small style="color:#999;">Driver Drowsy Detection System – Automated Alert</small>
          </div>
        </div>
        </body></html>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())

        print(f"[✅ EMAIL] Sent to {receiver}")
        return True
    except Exception as e:
        print(f"[❌ EMAIL] Failed: {e}")
        return False


# ══════════════════════════════════════════
#  CHANNEL 5 – Audio Alarm
# ══════════════════════════════════════════
def play_audio_alarm(sound_path="assets/sounds/alarm.mp3"):
    """
    Plays audio alarm through speakers.
    Falls back to terminal bell if no sound file.
    Put any alarm.mp3 in assets/sounds/ folder.
    Free alarm sounds: https://freesound.org
    """
    def _play():
        try:
            from playsound import playsound
            if os.path.exists(sound_path):
                playsound(sound_path)
                print("[✅ AUDIO] Alarm played.")
            else:
                # Fallback: terminal bell 3 times
                for _ in range(3):
                    print("\a", end="", flush=True)
                print("[⚠️  AUDIO] No alarm.mp3 found in assets/sounds/ – using terminal bell.")
                print("           Download a free alarm sound and save as assets/sounds/alarm.mp3")
        except Exception as e:
            print(f"[❌ AUDIO] Failed: {e}")

    threading.Thread(target=_play, daemon=True).start()


# ══════════════════════════════════════════
#  ALERT MANAGER – Central Dispatcher
# ══════════════════════════════════════════
class AlertManager:
    def __init__(self, cooldown=30):
        self.COOLDOWN_SECONDS = cooldown
        self._last_alert_time = None
        self._alert_count     = 0

    def _in_cooldown(self):
        if self._last_alert_time is None:
            return False
        elapsed = (datetime.now() - self._last_alert_time).seconds
        return elapsed < self.COOLDOWN_SECONDS

    def seconds_until_next(self):
        if self._last_alert_time is None:
            return 0
        elapsed = (datetime.now() - self._last_alert_time).seconds
        return max(0, self.COOLDOWN_SECONDS - elapsed)

    def trigger(self, channels=None, reason=""):
        if self._in_cooldown():
            print(f"[⏳ COOLDOWN] Next alert in {self.seconds_until_next()}s")
            return
        if channels is None:
            channels = ["audio"]
        self._last_alert_time = datetime.now()
        self._alert_count    += 1
        print(f"\n{'='*45}")
        print(f"  🚨 ALERT #{self._alert_count}")
        print(f"  Channels : {', '.join(channels)}")
        if reason:
            print(f"  Reason   : {reason}")
        print(f"  Time     : {self._last_alert_time.strftime('%H:%M:%S')}")
        print(f"{'='*45}")
        if "audio"    in channels: play_audio_alarm()
        if "sms"      in channels: threading.Thread(target=lambda: send_twilio_sms(f"DDS ALERT: {reason}"),        daemon=True).start()
        if "call"     in channels: threading.Thread(target=send_twilio_call,                                        daemon=True).start()
        if "whatsapp" in channels: threading.Thread(target=lambda: send_whatsapp_alert(f"*DDS ALERT*\n{reason}"),  daemon=True).start()
        if "email"    in channels: threading.Thread(target=send_email_alert,                                        daemon=True).start()