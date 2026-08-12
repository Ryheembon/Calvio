import smtplib
from email.message import EmailMessage

from .config import settings


def email_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send email via SMTP if configured; otherwise print to the terminal."""
    if not email_configured():
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

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.ehlo()
            if settings.smtp_port != 465:
                server.starttls()
                server.ehlo()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
        print(f"Email sent to {to_email}: {subject}")
    except Exception as exc:
        # Never block booking/login if email fails.
        print(f"EMAIL FAILED to {to_email}: {exc}")
