from __future__ import annotations

import smtplib
import uuid
from dataclasses import dataclass
from email.message import EmailMessage

from alphastream.email.render import render_email
from alphastream.types import DeliveryResult, EmailReport


class EmailSender:
    def send(self, report: EmailReport) -> DeliveryResult:
        raise NotImplementedError


@dataclass
class ConsoleEmailSender(EmailSender):
    def send(self, report: EmailReport) -> DeliveryResult:
        render_email(report)
        return DeliveryResult(success=True, provider_name="console", message_id=str(uuid.uuid4()), error=None)


@dataclass
class SMTPEmailSender(EmailSender):
    host: str
    port: int
    username: str
    password: str
    from_address: str
    to_address: str

    def send(self, report: EmailReport) -> DeliveryResult:
        html = render_email(report)
        message = EmailMessage()
        message["Subject"] = "AlphaStream Daily Picks"
        message["From"] = self.from_address
        message["To"] = self.to_address
        message.set_content("AlphaStream daily picks are available in HTML format.")
        message.add_alternative(html, subtype="html")
        try:
            with smtplib.SMTP(self.host, self.port, timeout=20) as smtp:
                smtp.starttls()
                smtp.login(self.username, self.password)
                smtp.send_message(message)
        except Exception as error:  # pragma: no cover - exercised in integration via stubs
            return DeliveryResult(success=False, provider_name="smtp", message_id=None, error=str(error))
        return DeliveryResult(success=True, provider_name="smtp", message_id=str(uuid.uuid4()), error=None)
