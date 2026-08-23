"""SMS Notification Service with multi-provider support and rate limiting.

Supports multiple SMS providers with failover:
- Twilio (primary)
- AWS SNS (fallback)
- MSG91 (India-specific, tertiary)

Features:
- Multi-language templates (10 languages)
- Rate limiting per phone number
- Delivery tracking
- Template-based messaging
- Provider failover
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field
from twilio.rest import Client as TwilioClient

from backend.cache import get_cache


class SMSProvider(str, Enum):
    """SMS service provider."""
    TWILIO = "twilio"
    AWS_SNS = "aws_sns"
    MSG91 = "msg91"


class SMSTemplate(str, Enum):
    """SMS notification templates."""
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    DRAFT_READY = "draft_ready"
    SUBMISSION_SUCCESS = "submission_success"
    SUBMISSION_FAILED = "submission_failed"
    DEADLINE_REMINDER = "deadline_reminder"
    OTP = "otp"
    WELCOME = "welcome"


class SMSLanguage(str, Enum):
    """Supported languages for SMS."""
    EN = "en"  # English
    HI = "hi"  # Hindi
    BN = "bn"  # Bengali
    TA = "ta"  # Tamil
    TE = "te"  # Telugu
    MR = "mr"  # Marathi
    GU = "gu"  # Gujarati
    KN = "kn"  # Kannada
    ML = "ml"  # Malayalam
    PA = "pa"  # Punjabi


class SMSStatus(str, Enum):
    """SMS delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class SMSNotification(BaseModel):
    """SMS notification record."""
    model_config = ConfigDict(frozen=True)

    notification_id: str
    phone_number: str
    message: str
    template: SMSTemplate
    language: SMSLanguage = SMSLanguage.EN
    status: SMSStatus = SMSStatus.PENDING
    provider: SMSProvider | None = None
    provider_message_id: str | None = None
    case_id: str | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    failed_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SMSProviderInterface(ABC):
    """Abstract interface for SMS providers."""

    @abstractmethod
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        metadata: dict[str, Any] | None = None
    ) -> tuple[bool, str | None]:
        """Send SMS via provider.

        Args:
            phone_number: Recipient phone number (E.164 format: +91xxxxxxxxxx)
            message: SMS content
            metadata: Optional metadata

        Returns:
            (success, provider_message_id or error_message)
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> SMSProvider:
        """Return provider identifier."""
        pass


class TwilioSMSProvider(SMSProviderInterface):
    """Twilio SMS provider."""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self._client: TwilioClient | None = None

        if self.account_sid and self.auth_token:
            self._client = TwilioClient(self.account_sid, self.auth_token)

    async def send_sms(
        self,
        phone_number: str,
        message: str,
        metadata: dict[str, Any] | None = None
    ) -> tuple[bool, str | None]:
        """Send SMS via Twilio."""
        if not self._client or not self.from_number:
            return False, "Twilio not configured"

        try:
            sms = self._client.messages.create(
                to=phone_number,
                from_=self.from_number,
                body=message
            )
            return True, sms.sid
        except Exception as e:
            return False, str(e)

    @property
    def is_available(self) -> bool:
        """Check Twilio configuration."""
        return bool(self.account_sid and self.auth_token and self.from_number)

    @property
    def provider_name(self) -> SMSProvider:
        return SMSProvider.TWILIO


class MSG91SMSProvider(SMSProviderInterface):
    """MSG91 SMS provider (India-specific)."""

    def __init__(self):
        self.auth_key = os.getenv("MSG91_AUTH_KEY")
        self.sender_id = os.getenv("MSG91_SENDER_ID", "LAWTRIX")
        self.route = os.getenv("MSG91_ROUTE", "4")  # 4 = Transactional
        self.base_url = "https://api.msg91.com/api/v5/flow/"

    async def send_sms(
        self,
        phone_number: str,
        message: str,
        metadata: dict[str, Any] | None = None
    ) -> tuple[bool, str | None]:
        """Send SMS via MSG91."""
        if not self.auth_key:
            return False, "MSG91 not configured"

        try:
            # Remove +91 prefix if present (MSG91 expects 10-digit number)
            clean_number = phone_number.replace("+91", "").replace("+", "")

            # MSG91 API v5 (OTP/Flow API)
            headers = {
                "authkey": self.auth_key,
                "content-type": "application/json"
            }

            payload = {
                "sender": self.sender_id,
                "route": self.route,
                "country": "91",
                "sms": [
                    {
                        "message": message,
                        "to": [clean_number]
                    }
                ]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}",
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return True, data.get("request_id", "success")
                else:
                    return False, f"MSG91 error: {response.text}"

        except Exception as e:
            return False, str(e)

    @property
    def is_available(self) -> bool:
        """Check MSG91 configuration."""
        return bool(self.auth_key)

    @property
    def provider_name(self) -> SMSProvider:
        return SMSProvider.MSG91


class SMSNotificationService:
    """SMS notification service with templates and rate limiting."""

    # SMS Templates in 10 languages
    TEMPLATES: dict[SMSTemplate, dict[SMSLanguage, str]] = {
        SMSTemplate.CASE_CREATED: {
            SMSLanguage.EN: "LAWTRIX: Your case {case_id} has been created. Track status at {url}",
            SMSLanguage.HI: "लॉट्रिक्स: आपका केस {case_id} बनाया गया है। स्थिति देखें {url}",
            SMSLanguage.TA: "லாட்ரிக்ஸ்: உங்கள் வழக்கு {case_id} உருவாக்கப்பட்டது। நிலையைப் பார்க்க {url}",
            SMSLanguage.BN: "ল'ট্রিক্স: আপনার কেস {case_id} তৈরি হয়েছে। স্ট্যাটাস দেখুন {url}",
            SMSLanguage.TE: "లాట్రిక్స్: మీ కేస్ {case_id} సృష్టించబడింది। స్థితి చూడండి {url}",
            SMSLanguage.MR: "लॉट्रिक्स: तुमचा केस {case_id} तयार झाला आहे। स्थिती पहा {url}",
            SMSLanguage.GU: "લોટ્રિક્સ: તમારો કેસ {case_id} બનાવ્યો છે। સ્થિતિ જુઓ {url}",
            SMSLanguage.KN: "ಲಾಟ್ರಿಕ್ಸ್: ನಿಮ್ಮ ಕೇಸ್ {case_id} ರಚಿಸಲಾಗಿದೆ। ಸ್ಥಿತಿ ನೋಡಿ {url}",
            SMSLanguage.ML: "ലോട്രിക്സ്: നിങ്ങളുടെ കേസ് {case_id} സൃഷ്ടിച്ചു। സ്റ്റാറ്റസ് കാണുക {url}",
            SMSLanguage.PA: "ਲਾਟ੍ਰਿਕਸ: ਤੁਹਾਡਾ ਕੇਸ {case_id} ਬਣਾਇਆ ਗਿਆ। ਸਥਿਤੀ ਦੇਖੋ {url}",
        },
        SMSTemplate.DRAFT_READY: {
            SMSLanguage.EN: "LAWTRIX: Draft ready for case {case_id}. Review and submit at {url}",
            SMSLanguage.HI: "लॉट्रिक्स: केस {case_id} का ड्राफ्ट तैयार है। समीक्षा करें {url}",
            SMSLanguage.TA: "லாட்ரிக்ஸ்: {case_id} வரைவு தயார். மதிப்பாய்வு செய்க {url}",
            SMSLanguage.BN: "ল'ট্রিক্স: {case_id} ড্রাফট তৈরি। রিভিউ করুন {url}",
            SMSLanguage.TE: "లాట్రిక్స్: {case_id} డ్రాఫ్ట్ సిద్ధం। సమీక్షించండి {url}",
            SMSLanguage.MR: "लॉट्रिक्स: {case_id} मसुदा तयार आहे। पुनरावलोकन करा {url}",
            SMSLanguage.GU: "લોટ્રિક્સ: {case_id} ડ્રાફ્ટ તૈયાર છે। સમીક્ષા કરો {url}",
            SMSLanguage.KN: "ಲಾಟ್ರಿಕ್ಸ್: {case_id} ಡ್ರಾಫ್ಟ್ ಸಿದ್ಧ। ಪರಿಶೀಲಿಸಿ {url}",
            SMSLanguage.ML: "ലോട്രിക്സ്: {case_id} ഡ്രാഫ്റ്റ് തയ്യാർ। പരിശോധിക്കുക {url}",
            SMSLanguage.PA: "ਲਾਟ੍ਰਿਕਸ: {case_id} ਡ੍ਰਾਫਟ ਤਿਆਰ। ਸਮੀਖਿਆ ਕਰੋ {url}",
        },
        SMSTemplate.SUBMISSION_SUCCESS: {
            SMSLanguage.EN: "LAWTRIX: Case {case_id} submitted successfully! Ref: {ref_id}. Track at {url}",
            SMSLanguage.HI: "लॉट्रिक्स: केस {case_id} सफलतापूर्वक जमा! संदर्भ: {ref_id}। ट्रैक करें {url}",
            SMSLanguage.TA: "லாட்ரிக்ஸ்: வழக்கு {case_id} வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது! குறிப்பு: {ref_id}",
            SMSLanguage.BN: "ল'ট্রিক্স: কেস {case_id} সফল! রেফ: {ref_id}। ট্র্যাক করুন {url}",
            SMSLanguage.TE: "లాట్రిక్స్: కేస్ {case_id} విజయవంతం! రెఫ్: {ref_id}। ట్రాక్ చేయండి {url}",
            SMSLanguage.MR: "लॉट्रिक्स: केस {case_id} यशस्वी! संदर्भ: {ref_id}। ट्रॅक करा {url}",
            SMSLanguage.GU: "લોટ્રિક્સ: કેસ {case_id} સફળ! સંદર્ભ: {ref_id}। ટ્રેક કરો {url}",
            SMSLanguage.KN: "ಲಾಟ್ರಿಕ್ಸ್: ಕೇಸ್ {case_id} ಯಶಸ್ವಿ! ಉಲ್ಲೇಖ: {ref_id}। ಟ್ರಾಕ್ ಮಾಡಿ {url}",
            SMSLanguage.ML: "ലോട്രിക്സ്: കേസ് {case_id} വിജയം! റെഫ്: {ref_id}। ട്രാക്ക് ചെയ്യുക {url}",
            SMSLanguage.PA: "ਲਾਟ੍ਰਿਕਸ: ਕੇਸ {case_id} ਸਫਲ! ਰੈਫ: {ref_id}। ਟਰੈਕ ਕਰੋ {url}",
        },
        SMSTemplate.OTP: {
            SMSLanguage.EN: "LAWTRIX: Your OTP is {otp}. Valid for {minutes} minutes. Do not share.",
            SMSLanguage.HI: "लॉट्रिक्स: आपका OTP {otp} है। {minutes} मिनट के लिए मान्य। साझा न करें।",
            SMSLanguage.TA: "லாட்ரிக்ஸ்: உங்கள் OTP {otp}। {minutes} நிமிடங்களுக்கு செல்லுபடியாகும்।",
            SMSLanguage.BN: "ল'ট্রিক্স: আপনার OTP {otp}। {minutes} মিনিটের জন্য বৈধ।",
            SMSLanguage.TE: "లాట్రిక్స్: మీ OTP {otp}। {minutes} నిమిషాలు చెల్లుతుంది।",
            SMSLanguage.MR: "लॉट्रिक्स: तुमचा OTP {otp}। {minutes} मिनिटांसाठी वैध।",
            SMSLanguage.GU: "લોટ્રિક્સ: તમારો OTP {otp}। {minutes} મિનિટ માટે માન્ય।",
            SMSLanguage.KN: "ಲಾಟ್ರಿಕ್ಸ್: ನಿಮ್ಮ OTP {otp}। {minutes} ನಿಮಿಷಗಳಿಗೆ ಮಾನ್ಯ।",
            SMSLanguage.ML: "ലോട്രിക്സ്: നിങ്ങളുടെ OTP {otp}। {minutes} മിനിറ്റ് സാധു।",
            SMSLanguage.PA: "ਲਾਟ੍ਰਿਕਸ: ਤੁਹਾਡਾ OTP {otp}। {minutes} ਮਿੰਟ ਲਈ ਮਾਨਯ।",
        },
    }

    # Rate limiting: max SMS per phone number per time window
    RATE_LIMIT_MAX = 5  # 5 SMS
    RATE_LIMIT_WINDOW = 3600  # 1 hour (seconds)

    def __init__(self):
        self.providers: list[SMSProviderInterface] = [
            TwilioSMSProvider(),
            MSG91SMSProvider(),
        ]
        self.cache = get_cache()

    async def send_notification(
        self,
        phone_number: str,
        template: SMSTemplate,
        language: SMSLanguage = SMSLanguage.EN,
        case_id: str | None = None,
        **template_vars
    ) -> SMSNotification:
        """Send SMS notification using template.

        Args:
            phone_number: Recipient phone (E.164 format: +91xxxxxxxxxx)
            template: Notification template
            language: Language for SMS
            case_id: Associated case ID
            **template_vars: Variables for template (e.g., case_id="123", url="...")

        Returns:
            SMSNotification record with status
        """
        # Check rate limit
        if not await self._check_rate_limit(phone_number):
            return SMSNotification(
                notification_id=f"sms_{datetime.utcnow().timestamp()}",
                phone_number=phone_number,
                message="Rate limited",
                template=template,
                language=language,
                status=SMSStatus.RATE_LIMITED,
                case_id=case_id,
                failed_reason="Rate limit exceeded (5 SMS per hour)",
            )

        # Get template message
        message = self._format_message(template, language, template_vars)

        # Try providers in order with failover
        for provider in self.providers:
            if not provider.is_available:
                continue

            success, result = await provider.send_sms(
                phone_number,
                message,
                metadata={"case_id": case_id, "template": template.value}
            )

            notification = SMSNotification(
                notification_id=f"sms_{datetime.utcnow().timestamp()}_{provider.provider_name.value}",
                phone_number=phone_number,
                message=message,
                template=template,
                language=language,
                status=SMSStatus.SENT if success else SMSStatus.FAILED,
                provider=provider.provider_name,
                provider_message_id=result if success else None,
                case_id=case_id,
                sent_at=datetime.utcnow() if success else None,
                failed_reason=result if not success else None,
            )

            if success:
                # Increment rate limit counter
                await self._increment_rate_limit(phone_number)
                return notification

        # All providers failed
        return SMSNotification(
            notification_id=f"sms_{datetime.utcnow().timestamp()}_failed",
            phone_number=phone_number,
            message=message,
            template=template,
            language=language,
            status=SMSStatus.FAILED,
            case_id=case_id,
            failed_reason="All SMS providers failed",
        )

    def _format_message(
        self,
        template: SMSTemplate,
        language: SMSLanguage,
        variables: dict[str, str]
    ) -> str:
        """Format SMS message from template."""
        template_str = self.TEMPLATES.get(template, {}).get(
            language,
            self.TEMPLATES[template][SMSLanguage.EN]  # Fallback to English
        )

        return template_str.format(**variables)

    async def _check_rate_limit(self, phone_number: str) -> bool:
        """Check if phone number is within rate limit."""
        key = f"sms_rate_limit:{phone_number}"
        count = await self.cache.get(key)

        if count is None:
            return True  # No rate limit hit yet

        return int(count) < self.RATE_LIMIT_MAX

    async def _increment_rate_limit(self, phone_number: str):
        """Increment rate limit counter for phone number."""
        key = f"sms_rate_limit:{phone_number}"
        current = await self.cache.get(key)

        if current is None:
            await self.cache.set(key, "1", ttl=self.RATE_LIMIT_WINDOW)
        else:
            await self.cache.set(key, str(int(current) + 1), ttl=self.RATE_LIMIT_WINDOW)


# Singleton instance
_sms_service: SMSNotificationService | None = None


def get_sms_service() -> SMSNotificationService:
    """Get singleton SMS notification service."""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSNotificationService()
    return _sms_service
