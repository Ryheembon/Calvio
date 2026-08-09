import smtplib
from email.message import EmailMessage

from .config import settings


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send email via SMTP if configured; otherwise print to the terminal."""
    if not settings.smtp_host:
        print("\n=== EMAIL (dev mode) ===")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(body)
        print("========================\n")
        return

    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
