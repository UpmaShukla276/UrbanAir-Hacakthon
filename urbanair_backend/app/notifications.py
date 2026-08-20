"""
Email Sending (optional)
==========================
Sends alert emails via SMTP. Requires the user's own email + app password
in a .env file (see .env.example) -- this is NOT a government SMS/push
gateway integration, just a demo-ready way to show an alert actually
being delivered somewhere real.

For a production deployment, replace this with whatever official
notification channel DPCC/MCD actually uses (SMS gateway, internal
dashboard alert queue, etc.) -- this module exists so the hackathon demo
can show a real, working "Send Alert" button, not a fake one.
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", "")


def is_configured():
    return bool(SMTP_EMAIL and SMTP_APP_PASSWORD)


def send_email(to_email, subject, body):
    if not is_configured():
        raise RuntimeError(
            "SMTP not configured. Set SMTP_EMAIL and SMTP_APP_PASSWORD in .env "
            "(for Gmail: enable 2FA, then create an App Password at "
            "myaccount.google.com/apppasswords)."
        )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [to_email], msg.as_string())

    return {"sent": True, "to": to_email}
