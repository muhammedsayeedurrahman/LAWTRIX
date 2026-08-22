"""DigiLocker document provider with OAuth 2.0 integration.

Provides secure access to user documents stored in DigiLocker with explicit consent.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


class DigiLockerDocumentType(str, Enum):
    """Document types available in DigiLocker."""
    AADHAAR = "aadhaar"
    PAN = "pan"
    DRIVING_LICENSE = "driving_license"
    VEHICLE_RC = "vehicle_rc"
    EDUCATION_CERTIFICATE = "education_certificate"
    VACCINATION_CERTIFICATE = "vaccination_certificate"
    INSURANCE_POLICY = "insurance_policy"


class DigiLockerDocument(BaseModel):
    """DigiLocker document metadata."""
    model_config = ConfigDict(frozen=True)

    document_id: str = Field(..., description="DigiLocker document identifier")
    document_type: DigiLockerDocumentType
    document_name: str
    issuer: str = Field(..., description="Issuing authority")
    issue_date: str | None = None
    document_uri: str = Field(..., description="DigiLocker URI")

    # Access metadata
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    access_expires_at: datetime | None = None


class DigiLockerAccessToken(BaseModel):
    """DigiLocker OAuth access token."""
    model_config = ConfigDict(frozen=True)

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")
    refresh_token: str | None = None
    scope: str = Field(..., description="Granted scopes")

    # Metadata
    obtained_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        expiry_time = self.obtained_at + timedelta(seconds=self.expires_in)
        return datetime.utcnow() >= expiry_time


class DigiLockerConsentRequest(BaseModel):
    """User consent request for DigiLocker access."""
    model_config = ConfigDict(frozen=True)

    user_id: str
    requested_scopes: list[DigiLockerDocumentType] = Field(..., description="Document types requested")
    purpose: str = Field(..., description="Why access is needed")
    case_id: str | None = Field(None, description="Associated case ID")

    # Consent metadata
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=30)
    )


class DigiLockerConsent(BaseModel):
    """User consent record for DigiLocker access."""
    model_config = ConfigDict(frozen=True)

    consent_id: str
    user_id: str
    granted_scopes: list[DigiLockerDocumentType]
    purpose: str
    case_id: str | None = None

    # Consent lifecycle
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    revoked_at: datetime | None = None

    # Access record
    documents_accessed: list[str] = Field(default_factory=list, description="Document IDs accessed")
    last_accessed_at: datetime | None = None

    @property
    def is_valid(self) -> bool:
        """Check if consent is still valid."""
        if self.revoked_at:
            return False
        return datetime.utcnow() < self.expires_at


class DigiLockerProvider:
    """DigiLocker document provider with OAuth 2.0.

    Handles user authorization, document access, and consent management.
    """

    def __init__(self):
        self.client_id = os.getenv("DIGILOCKER_CLIENT_ID")
        self.client_secret = os.getenv("DIGILOCKER_CLIENT_SECRET")
        self.redirect_uri = os.getenv(
            "DIGILOCKER_REDIRECT_URI",
            "https://lawtrix.app/auth/digilocker/callback"
        )
        self.sandbox_mode = os.getenv("DIGILOCKER_SANDBOX", "true").lower() == "true"

        # DigiLocker endpoints
        if self.sandbox_mode:
            self.base_url = "https://api.digitallocker.gov.in/sandbox"
        else:
            self.base_url = "https://api.digitallocker.gov.in/public"

        self.auth_url = f"{self.base_url}/oauth2/1/authorize"
        self.token_url = f"{self.base_url}/oauth2/1/token"
        self.api_url = f"{self.base_url}/api/1.0"

    @property
    def is_available(self) -> bool:
        """Check if DigiLocker provider is configured."""
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(
        self,
        consent_request: DigiLockerConsentRequest,
        state: str,
    ) -> str:
        """Generate DigiLocker authorization URL for user consent.

        Args:
            consent_request: Consent request with requested scopes
            state: State parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        if not self.is_available:
            raise ValueError("DigiLocker client credentials not configured")

        # Map document types to DigiLocker scopes
        scope_mapping = {
            DigiLockerDocumentType.AADHAAR: "aadhaar",
            DigiLockerDocumentType.PAN: "pan",
            DigiLockerDocumentType.DRIVING_LICENSE: "dl",
            DigiLockerDocumentType.VEHICLE_RC: "vehicle",
            DigiLockerDocumentType.EDUCATION_CERTIFICATE: "education",
        }

        scopes = []
        for doc_type in consent_request.requested_scopes:
            scope = scope_mapping.get(doc_type)
            if scope:
                scopes.append(scope)

        scope_str = " ".join(scopes) if scopes else "profile"

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": scope_str,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.auth_url}?{query_string}"

    async def exchange_code_for_token(
        self,
        authorization_code: str,
    ) -> DigiLockerAccessToken:
        """Exchange authorization code for access token.

        Args:
            authorization_code: Code from DigiLocker callback

        Returns:
            DigiLockerAccessToken

        Raises:
            httpx.HTTPError: If token exchange fails
        """
        if not self.is_available:
            raise ValueError("DigiLocker client credentials not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()

            return DigiLockerAccessToken(
                access_token=data["access_token"],
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in", 3600),
                refresh_token=data.get("refresh_token"),
                scope=data.get("scope", ""),
            )

    async def list_documents(
        self,
        access_token: DigiLockerAccessToken,
    ) -> list[DigiLockerDocument]:
        """List documents available in user's DigiLocker.

        Args:
            access_token: Valid DigiLocker access token

        Returns:
            List of available documents

        Raises:
            httpx.HTTPError: If API call fails
        """
        if access_token.is_expired:
            raise ValueError("Access token has expired")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/issued",
                headers={"Authorization": f"Bearer {access_token.access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            documents = []
            for item in data.get("items", []):
                # Map DigiLocker response to our model
                doc_type = self._map_digilocker_type(item.get("doctype", ""))

                documents.append(DigiLockerDocument(
                    document_id=item["uri"],
                    document_type=doc_type,
                    document_name=item.get("name", ""),
                    issuer=item.get("issuer", ""),
                    issue_date=item.get("date"),
                    document_uri=item["uri"],
                ))

            return documents

    async def get_document_content(
        self,
        access_token: DigiLockerAccessToken,
        document_uri: str,
    ) -> bytes:
        """Fetch document content from DigiLocker.

        Args:
            access_token: Valid DigiLocker access token
            document_uri: DigiLocker document URI

        Returns:
            Document content as bytes

        Raises:
            httpx.HTTPError: If API call fails
        """
        if access_token.is_expired:
            raise ValueError("Access token has expired")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/file/{document_uri}",
                headers={"Authorization": f"Bearer {access_token.access_token}"},
            )
            response.raise_for_status()
            return response.content

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> DigiLockerAccessToken:
        """Refresh access token using refresh token.

        Args:
            refresh_token: DigiLocker refresh token

        Returns:
            New DigiLockerAccessToken

        Raises:
            httpx.HTTPError: If refresh fails
        """
        if not self.is_available:
            raise ValueError("DigiLocker client credentials not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()

            return DigiLockerAccessToken(
                access_token=data["access_token"],
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in", 3600),
                refresh_token=data.get("refresh_token", refresh_token),
                scope=data.get("scope", ""),
            )

    def _map_digilocker_type(self, digilocker_type: str) -> DigiLockerDocumentType:
        """Map DigiLocker document type to our enum.

        Args:
            digilocker_type: DigiLocker document type string

        Returns:
            DigiLockerDocumentType
        """
        type_mapping = {
            "ADHAR": DigiLockerDocumentType.AADHAAR,
            "PAN": DigiLockerDocumentType.PAN,
            "DRIVING_LICENSE": DigiLockerDocumentType.DRIVING_LICENSE,
            "VAHAN": DigiLockerDocumentType.VEHICLE_RC,
            "EDUCATION": DigiLockerDocumentType.EDUCATION_CERTIFICATE,
            "COWIN": DigiLockerDocumentType.VACCINATION_CERTIFICATE,
        }

        return type_mapping.get(digilocker_type.upper(), DigiLockerDocumentType.AADHAAR)


class DigiLockerConsentManager:
    """Manages user consent for DigiLocker access."""

    def __init__(self):
        # In production, this would use database storage
        self._consents: dict[str, DigiLockerConsent] = {}

    async def request_consent(
        self,
        consent_request: DigiLockerConsentRequest,
    ) -> tuple[str, str]:
        """Create consent request and generate authorization URL.

        Args:
            consent_request: Consent request details

        Returns:
            (consent_id, authorization_url)
        """
        import uuid

        consent_id = f"consent_{uuid.uuid4()}"
        state = f"{consent_id}_{consent_request.user_id}"

        provider = DigiLockerProvider()
        auth_url = provider.get_authorization_url(consent_request, state)

        return consent_id, auth_url

    async def grant_consent(
        self,
        consent_id: str,
        user_id: str,
        granted_scopes: list[DigiLockerDocumentType],
        purpose: str,
        expires_at: datetime,
        case_id: str | None = None,
    ) -> DigiLockerConsent:
        """Grant consent for DigiLocker access.

        Args:
            consent_id: Consent identifier
            user_id: User granting consent
            granted_scopes: Document types granted access to
            purpose: Purpose of access
            expires_at: When consent expires
            case_id: Associated case ID if any

        Returns:
            DigiLockerConsent record
        """
        consent = DigiLockerConsent(
            consent_id=consent_id,
            user_id=user_id,
            granted_scopes=granted_scopes,
            purpose=purpose,
            case_id=case_id,
            expires_at=expires_at,
        )

        self._consents[consent_id] = consent
        return consent

    async def revoke_consent(self, consent_id: str) -> DigiLockerConsent:
        """Revoke user consent.

        Args:
            consent_id: Consent to revoke

        Returns:
            Updated DigiLockerConsent

        Raises:
            KeyError: If consent not found
        """
        consent = self._consents.get(consent_id)
        if not consent:
            raise KeyError(f"Consent not found: {consent_id}")

        revoked_consent = consent.model_copy(
            update={"revoked_at": datetime.utcnow()}
        )

        self._consents[consent_id] = revoked_consent
        return revoked_consent

    async def get_consent(self, consent_id: str) -> DigiLockerConsent | None:
        """Get consent by ID.

        Args:
            consent_id: Consent identifier

        Returns:
            DigiLockerConsent or None if not found
        """
        return self._consents.get(consent_id)

    async def get_user_consents(self, user_id: str) -> list[DigiLockerConsent]:
        """Get all consents for a user.

        Args:
            user_id: User identifier

        Returns:
            List of user's consents
        """
        return [
            consent for consent in self._consents.values()
            if consent.user_id == user_id
        ]

    async def record_document_access(
        self,
        consent_id: str,
        document_id: str,
    ) -> DigiLockerConsent:
        """Record that a document was accessed under consent.

        Args:
            consent_id: Consent identifier
            document_id: Document that was accessed

        Returns:
            Updated DigiLockerConsent

        Raises:
            KeyError: If consent not found
            ValueError: If consent not valid
        """
        consent = self._consents.get(consent_id)
        if not consent:
            raise KeyError(f"Consent not found: {consent_id}")

        if not consent.is_valid:
            raise ValueError(f"Consent is not valid: {consent_id}")

        new_accessed = list(consent.documents_accessed) + [document_id]

        updated_consent = consent.model_copy(
            update={
                "documents_accessed": new_accessed,
                "last_accessed_at": datetime.utcnow(),
            }
        )

        self._consents[consent_id] = updated_consent
        return updated_consent
