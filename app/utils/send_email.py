import os
import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

def send_email(subject: str, body: str, to_emails: list, from_email: str = None, attachments: list = None):
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")

    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS]):
        logger.error("SMTP configuration incomplete")
        raise RuntimeError("SMTP configuration incomplete")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email or SMTP_USER
    msg["To"] = ", ".join(to_emails if isinstance(to_emails, (list,tuple)) else [to_emails])
    msg.set_content(body)

    if attachments:
        for name, data, mime in attachments:
            try:
                msg.add_attachment(data, maintype=mime.split("/")[0], subtype=mime.split("/")[1], filename=name)
            except Exception:
                logger.exception("Failed to attach file")
                raise

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            if SMTP_PORT == 587:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
            logger.info(f"Email sent to {msg['To']}")
    except Exception:
        logger.exception("Email sending failed")
        raise
