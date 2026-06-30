"""SMTP email delivery service."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..core.config import get_settings


class EmailService:
    """Small SMTP abstraction for transactional notifications."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_enabled(self) -> bool:
        return bool(
            self.settings.SMTP_ENABLED
            and self.settings.SMTP_SERVER
            and self.settings.SMTP_PORT
            and self.settings.SENDER_EMAIL
        )

    def send(self, recipient_email: str, subject: str, body: str) -> bool:
        """Send one plain text email through configured SMTP transport."""
        if not self.is_enabled() or not recipient_email:
            return False

        message = EmailMessage()
        message["From"] = f"{self.settings.SMTP_FROM_NAME} <{self.settings.SENDER_EMAIL}>"
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.settings.SMTP_SERVER, self.settings.SMTP_PORT, timeout=15) as smtp:
                if self.settings.SMTP_USE_TLS:
                    smtp.starttls()
                if self.settings.SMTP_USERNAME:
                    smtp.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                smtp.send_message(message)
            return True
        except Exception:
            return False

    def send_to_recipients(self, recipients: list[str], subject: str, body: str) -> int:
        """Send an email to multiple recipients. Returns the count of successful sends."""
        sent = 0
        for recipient in recipients:
            if self.send(recipient, subject, body):
                sent += 1
        return sent

