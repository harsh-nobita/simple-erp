import smtplib
from email.message import EmailMessage
from typing import Optional

# Minimal email sender helper. For production use, swap to Flask-Mail or transactional providers (SendGrid, SES).

def send_email(subject: str, body: str, to: str, from_addr: str, smtp_host='localhost', smtp_port=25, username: Optional[str]=None, password: Optional[str]=None, use_tls=False):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as s:
        if use_tls:
            s.starttls()
        if username and password:
            s.login(username, password)
        s.send_message(msg)


def send_sms_placeholder(number: str, text: str):
    """Placeholder for SMS/WhatsApp integration. Replace with Twilio/MessageBird API calls."""
    # Implement provider integration here.
    print(f"[SMS placeholder] to={number} text={text}")
