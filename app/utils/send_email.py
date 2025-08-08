import smtplib
from email.message import EmailMessage
import os

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

def send_email(subject, body, to_emails, from_email=SMTP_USER, attachments=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails if isinstance(to_emails, (list,tuple)) else [to_emails])
    msg.set_content(body)

    if attachments:
        for name, data, mime in attachments:
            msg.add_attachment(data, maintype=mime.split("/")[0], subtype=mime.split("/")[1], filename=name)

    try:
        server = smtplib.SMTP(SMTP_HOST, int(SMTP_PORT), timeout=10)
        server.ehlo()
        if int(SMTP_PORT) == 587:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass
