# phase1_core/alerter.py
# ─────────────────────────────────────────
#  All Alert Channels – Phase 1 & 2
#  Audio loops continuously until driver wakes
#  Calls/SMS/Email fire after confirmed delay
# ─────────────────────────────────────────

import os
import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def send_twilio_call():
    try:
        from twilio.rest import Client
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        call = client.calls.create(
            twiml='''<Response>
                <Say voice="alice" loop="3">
                    Warning! Warning! The driver appears to be drowsy.
                    Please pull over immediately and take a rest.
                    This is an automated alert from the Driver Drowsy Detection System.
                </Say>
            </Response>''',
            to=os.getenv("ALERT_PHONE_NUMBER"),
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
        )
        print(f"[OK CALL] Initiated -> {call.sid}")
    except Exception as e:
        print(f"[ERR CALL] {e}")


def send_twilio_sms(message=None):
    try:
        from twilio.rest import Client
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        if not message:
            message = f"DDS ALERT - Drowsiness confirmed! Time: {now}. Check on the driver immediately."
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        msg = client.messages.create(
            body=message,
            to=os.getenv("ALERT_PHONE_NUMBER"),
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
        )
        print(f"[OK SMS] Sent -> {msg.sid}")
    except Exception as e:
        print(f"[ERR SMS] {e}")


def send_whatsapp_alert(message=None):
    try:
        from twilio.rest import Client
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        if not message:
            message = f"DDS ALERT\nDrowsiness Confirmed!\nTime: {now}\nCheck on the driver immediately!"
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(
            body=message,
            to=os.getenv("WHATSAPP_TO"),
            from_=os.getenv("WHATSAPP_FROM"),
        )
        print("[OK WHATSAPP] Sent.")
    except Exception as e:
        print(f"[ERR WHATSAPP] {e}")


def send_email_alert(reason=""):
    try:
        sender   = os.getenv("EMAIL_SENDER")
        password = os.getenv("EMAIL_PASSWORD")
        receiver = os.getenv("EMAIL_RECEIVER")
        now      = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = f"DDS Alert - Drowsiness Confirmed at {now}"
        msg["From"]    = sender
        msg["To"]      = receiver
        text = f"DROWSINESS CONFIRMED\nTime: {now}\nSignals: {reason}\nCheck on the driver immediately!"
        html = f"""<html><body>
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;
                    border:2px solid #e53e3e;border-radius:8px;overflow:hidden;">
          <div style="background:#e53e3e;padding:16px;text-align:center;">
            <h2 style="color:white;margin:0;">DROWSINESS CONFIRMED</h2>
          </div>
          <div style="padding:20px;background:#fff8f8;">
            <p><strong>Time:</strong> {now}</p>
            <p><strong>Signals:</strong> {reason}</p>
            <p style="color:#e53e3e;"><strong>Check on the driver immediately!</strong></p>
          </div>
        </div></body></html>"""
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html,  "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"[OK EMAIL] Sent to {receiver}")
    except Exception as e:
        print(f"[ERR EMAIL] {e}")


class AudioAlarm:
    """
    Continuous looping audio alarm.
    start() - begins looping
    stop()  - stops when driver wakes up
    """
    def __init__(self, sound_path="assets/sounds/alarm.mp3"):
        self.sound_path = sound_path
        self._playing   = False
        self._thread    = None

    def start(self):
        if self._playing:
            return
        self._playing = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[AUDIO] Alarm started - looping.")

    def stop(self):
        if self._playing:
            self._playing = False
            print("[AUDIO] Alarm stopped - driver awake.")

    def _loop(self):
        while self._playing:
            try:
                from playsound import playsound
                if os.path.exists(self.sound_path):
                    playsound(self.sound_path, block=True)
                else:
                    print("\a", end="", flush=True)
                    time.sleep(1)
            except Exception:
                time.sleep(1)


class AlertManager:
    """
    Two-stage alert system:

    Stage 1 - Any drowsiness signal detected:
      -> Audio alarm starts looping immediately

    Stage 2 - Drowsiness sustained for CONFIRM_SECONDS (default 6s):
      -> Call + SMS + WhatsApp + Email fire once
      -> Repeats every CALL_COOLDOWN seconds if still drowsy

    Audio stops automatically when driver wakes up.
    """

    CONFIRM_SECONDS = 8    # seconds before calls fire
    CALL_COOLDOWN   = 60   # min seconds between repeated calls

    def __init__(self, cooldown=None):
        self.CALL_COOLDOWN    = cooldown or self.CALL_COOLDOWN
        self._audio           = AudioAlarm()
        self._drowsy_since    = None
        self._call_sent_at    = None
        self._alert_count     = 0
        self._last_print      = -1

    def update(self, is_drowsy, alert_score=0, reason=""):
        """
        Call every frame.
        is_drowsy : bool  - True if any drowsiness signal active
        reason    : str   - signal description for SMS/email
        """
        now = datetime.now()

        if is_drowsy:
            # Stage 1 - audio starts immediately
            self._audio.start()

            # Track drowsy start time
            if self._drowsy_since is None:
                self._drowsy_since = now
                print(f"[WARNING] Drowsiness detected - audio started.")
                print(f"[WAITING] Calls/SMS fire in {self.CONFIRM_SECONDS}s if sustained...")

            seconds_drowsy = (now - self._drowsy_since).total_seconds()
            remaining      = max(0, self.CONFIRM_SECONDS - seconds_drowsy)

            # Print countdown every second
            if int(seconds_drowsy) != self._last_print:
                self._last_print = int(seconds_drowsy)
                if seconds_drowsy < self.CONFIRM_SECONDS:
                    print(f"[COUNTDOWN] {int(seconds_drowsy)}s / {self.CONFIRM_SECONDS}s - call fires in {int(remaining)+1}s")

            # Stage 2 - fire calls after delay
            if seconds_drowsy >= self.CONFIRM_SECONDS:
                call_ok = (
                    self._call_sent_at is None or
                    (now - self._call_sent_at).total_seconds() >= self.CALL_COOLDOWN
                )
                if call_ok:
                    self._alert_count += 1
                    self._call_sent_at = now
                    print(f"\n{'='*48}")
                    print(f"  CRITICAL ALERT #{self._alert_count} FIRING")
                    print(f"  Reason  : {reason}")
                    print(f"  Drowsy  : {seconds_drowsy:.1f}s")
                    print(f"  Time    : {now.strftime('%H:%M:%S')}")
                    print(f"{'='*48}\n")
                    threading.Thread(target=send_twilio_call,                                      daemon=True).start()
                    threading.Thread(target=lambda: send_twilio_sms(f"DDS ALERT: {reason}"),       daemon=True).start()
                    threading.Thread(target=lambda: send_whatsapp_alert(f"DDS ALERT\n{reason}"),   daemon=True).start()
                    threading.Thread(target=lambda: send_email_alert(reason=reason),               daemon=True).start()

        else:
            # Driver woke up
            if self._drowsy_since is not None:
                elapsed = (now - self._drowsy_since).total_seconds()
                print(f"[AWAKE] Driver awake after {elapsed:.1f}s - alarm stopped.")
            self._audio.stop()
            self._drowsy_since = None
            self._last_print   = -1

    def get_countdown(self):
        """Seconds remaining before critical alert fires."""
        if self._drowsy_since is None:
            return self.CONFIRM_SECONDS
        elapsed = (datetime.now() - self._drowsy_since).total_seconds()
        return max(0, self.CONFIRM_SECONDS - elapsed)

    def is_confirmed(self):
        """True if drowsy long enough for critical alert."""
        if self._drowsy_since is None:
            return False
        return (datetime.now() - self._drowsy_since).total_seconds() >= self.CONFIRM_SECONDS