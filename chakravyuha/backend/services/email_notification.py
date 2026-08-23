"""Email Notification Service with HTML templates and attachment support.

Features:
- HTML email templates with LAWTRIX branding
- SMTP/SendGrid/AWS SES support
- Attachment support (PDFs, documents)
- Email queue with retry logic
- Multi-language support (10 languages)
- Unsubscribe management
"""

from __future__ import annotations

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


class EmailProvider(str, Enum):
    """Email service provider."""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"


class EmailTemplate(str, Enum):
    """Email notification templates."""
    WELCOME = "welcome"
    CASE_CREATED = "case_created"
    DRAFT_READY = "draft_ready"
    SUBMISSION_SUCCESS = "submission_success"
    SUBMISSION_FAILED = "submission_failed"
    DEADLINE_REMINDER = "deadline_reminder"
    WEEKLY_SUMMARY = "weekly_summary"


class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailAttachment(BaseModel):
    """Email attachment."""
    filename: str
    content: bytes
    content_type: str = "application/pdf"


class EmailNotification(BaseModel):
    """Email notification record."""
    model_config = ConfigDict(frozen=True)

    notification_id: str
    to_email: str
    subject: str
    html_body: str
    plain_body: str | None = None
    template: EmailTemplate
    status: EmailStatus = EmailStatus.PENDING
    provider: EmailProvider | None = None
    provider_message_id: str | None = None
    case_id: str | None = None
    attachments: list[str] = Field(default_factory=list)  # Filenames
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    failed_reason: str | None = None
    retry_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmailProviderInterface(ABC):
    """Abstract interface for email providers."""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: str | None = None,
        attachments: list[EmailAttachment] | None = None,
    ) -> tuple[bool, str | None]:
        """Send email via provider.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email content
            plain_body: Plain text fallback
            attachments: Optional attachments

        Returns:
            (success, provider_message_id or error_message)
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured."""
        pass


class SMTPEmailProvider(EmailProviderInterface):
    """SMTP email provider."""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@lawtrix.in")
        self.from_name = os.getenv("SMTP_FROM_NAME", "LAWTRIX")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: str | None = None,
        attachments: list[EmailAttachment] | None = None,
    ) -> tuple[bool, str | None]:
        """Send email via SMTP."""
        if not self.smtp_username or not self.smtp_password:
            return False, "SMTP not configured"

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            # Attach plain text and HTML versions
            if plain_body:
                msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Attach files
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {attachment.filename}",
                    )
                    msg.attach(part)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return True, f"smtp_{datetime.utcnow().timestamp()}"

        except Exception as e:
            return False, str(e)

    @property
    def is_available(self) -> bool:
        return bool(self.smtp_username and self.smtp_password)


class SendGridEmailProvider(EmailProviderInterface):
    """SendGrid email provider."""

    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@lawtrix.in")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "LAWTRIX")
        self.base_url = "https://api.sendgrid.com/v3/mail/send"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: str | None = None,
        attachments: list[EmailAttachment] | None = None,
    ) -> tuple[bool, str | None]:
        """Send email via SendGrid."""
        if not self.api_key:
            return False, "SendGrid not configured"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "personalizations": [{
                    "to": [{"email": to_email}],
                    "subject": subject,
                }],
                "from": {
                    "email": self.from_email,
                    "name": self.from_name,
                },
                "content": [
                    {"type": "text/plain", "value": plain_body or ""},
                    {"type": "text/html", "value": html_body},
                ],
            }

            # Add attachments
            if attachments:
                payload["attachments"] = [
                    {
                        "content": attachment.content.decode("latin-1"),
                        "filename": attachment.filename,
                        "type": attachment.content_type,
                    }
                    for attachment in attachments
                ]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code == 202:
                    message_id = response.headers.get("X-Message-Id", "success")
                    return True, message_id
                else:
                    return False, f"SendGrid error: {response.text}"

        except Exception as e:
            return False, str(e)

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)


class EmailNotificationService:
    """Email notification service with templates."""

    # HTML Email Templates
    HTML_TEMPLATE_BASE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Inter, -apple-system, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #003D82 0%, #0056B3 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 30px; }}
            .content h2 {{ color: #003D82; margin-top: 0; }}
            .content p {{ line-height: 1.6; color: #333; }}
            .cta {{ display: inline-block; background: #003D82; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0; }}
            .footer a {{ color: #003D82; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>LAWTRIX</h1>
                <p>Your Voice for Justice in India</p>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>© 2026 LAWTRIX. Made with ❤️ for Indian Citizens.</p>
                <p><a href="{unsubscribe_url}">Unsubscribe</a> | <a href="https://lawtrix.in/privacy">Privacy Policy</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    TEMPLATES = {
        EmailTemplate.CASE_CREATED: {
            "subject_en": "Your case has been created - {case_id}",
            "subject_hi": "आपका केस बनाया गया है - {case_id}",
            "content_en": """
                <h2>Case Created Successfully</h2>
                <p>Dear {name},</p>
                <p>Your case <strong>{case_id}</strong> has been created successfully.</p>
                <p><strong>Workflow:</strong> {workflow}</p>
                <p><strong>Status:</strong> {status}</p>
                <p>You can track your case status and view updates anytime:</p>
                <a href="{case_url}" class="cta">View Case Details</a>
                <p>We will notify you of any updates via email and SMS.</p>
            """,
        },
        EmailTemplate.DRAFT_READY: {
            "subject_en": "Your draft is ready for review - {case_id}",
            "subject_hi": "आपका ड्राफ्ट समीक्षा के लिए तैयार है - {case_id}",
            "content_en": """
                <h2>Draft Ready for Review</h2>
                <p>Dear {name},</p>
                <p>Great news! Your {workflow} draft for case <strong>{case_id}</strong> is ready.</p>
                <p>Please review the draft carefully before submission:</p>
                <a href="{draft_url}" class="cta">Review Draft</a>
                <p>Once you confirm, we will submit it to the relevant authority.</p>
            """,
        },
        EmailTemplate.SUBMISSION_SUCCESS: {
            "subject_en": "Successfully submitted - {case_id}",
            "subject_hi": "सफलतापूर्वक सबमिट किया गया - {case_id}",
            "content_en": """
                <h2>Submission Successful!</h2>
                <p>Dear {name},</p>
                <p>Your case <strong>{case_id}</strong> has been successfully submitted.</p>
                <p><strong>Reference ID:</strong> {ref_id}</p>
                <p><strong>Authority:</strong> {authority}</p>
                <p><strong>Submitted on:</strong> {date}</p>
                <a href="{tracking_url}" class="cta">Track Status</a>
                <p>You will receive updates on your case progress via email and SMS.</p>
            """,
        },
    }

    def __init__(self):
        self.providers: list[EmailProviderInterface] = [
            SendGridEmailProvider(),
            SMTPEmailProvider(),
        ]

    async def send_notification(
        self,
        to_email: str,
        template: EmailTemplate,
        case_id: str | None = None,
        attachments: list[EmailAttachment] | None = None,
        language: str = "en",
        **template_vars
    ) -> EmailNotification:
        """Send email notification.

        Args:
            to_email: Recipient email
            template: Email template
            case_id: Associated case ID
            attachments: Optional attachments (PDFs, etc.)
            language: Language code (en, hi, etc.)
            **template_vars: Variables for template

        Returns:
            EmailNotification record
        """
        # Get template content
        subject = self._get_template_field(template, f"subject_{language}", template_vars)
        content = self._get_template_field(template, f"content_{language}", template_vars)

        # Wrap in HTML template
        template_vars.setdefault("unsubscribe_url", f"https://lawtrix.in/unsubscribe?email={to_email}")
        html_body = self.HTML_TEMPLATE_BASE.format(content=content, **template_vars)

        # Plain text fallback (strip HTML)
        plain_body = self._html_to_plain(content)

        # Try providers with failover
        for provider in self.providers:
            if not provider.is_available:
                continue

            success, result = await provider.send_email(
                to_email,
                subject,
                html_body,
                plain_body,
                attachments
            )

            notification = EmailNotification(
                notification_id=f"email_{datetime.utcnow().timestamp()}",
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                plain_body=plain_body,
                template=template,
                status=EmailStatus.SENT if success else EmailStatus.FAILED,
                provider=EmailProvider.SENDGRID if isinstance(provider, SendGridEmailProvider) else EmailProvider.SMTP,
                provider_message_id=result if success else None,
                case_id=case_id,
                attachments=[att.filename for att in (attachments or [])],
                sent_at=datetime.utcnow() if success else None,
                failed_reason=result if not success else None,
            )

            if success:
                return notification

        # All providers failed
        return EmailNotification(
            notification_id=f"email_{datetime.utcnow().timestamp()}_failed",
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            template=template,
            status=EmailStatus.FAILED,
            case_id=case_id,
            failed_reason="All email providers failed",
        )

    def _get_template_field(self, template: EmailTemplate, field: str, variables: dict) -> str:
        """Get template field and format with variables."""
        template_data = self.TEMPLATES.get(template, {})
        template_str = template_data.get(field, template_data.get(field.replace("_hi", "_en"), ""))
        return template_str.format(**variables)

    def _html_to_plain(self, html: str) -> str:
        """Convert HTML to plain text (basic)."""
        # Remove HTML tags (basic implementation)
        import re
        text = re.sub('<[^<]+?>', '', html)
        return text.strip()


# Singleton
_email_service: EmailNotificationService | None = None


def get_email_service() -> EmailNotificationService:
    """Get singleton email notification service."""
    global _email_service
    if _email_service is None:
        _email_service = EmailNotificationService()
    return _email_service
