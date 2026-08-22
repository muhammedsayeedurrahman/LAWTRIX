"""Scheme provider abstraction with multiple data sources.

Provides unified interface for scheme data from:
- Local verified schemes (JSON)
- API Setu myScheme API (when authorized)
- data.gov.in (supplementary)
- Other official sources

Implements fallback pattern: API → local verified data.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from backend.cache import get_cache
from backend.config import PROJECT_ROOT


class ProviderType(str, Enum):
    """Type of scheme data provider."""
    LOCAL = "local"
    API_LIVE = "api_live"
    OPEN_DATA = "open_data"


class SchemeBase(BaseModel):
    """Base scheme model compatible with all providers."""
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    short_name: str = ""
    description: str
    benefit_summary: str = ""
    target_group: str = ""
    jurisdiction: dict[str, Any] = Field(default_factory=dict)
    eligibility: dict[str, Any] = Field(default_factory=dict)
    required_documents: list[str] = Field(default_factory=list)
    application_url: str | None = None
    official_portal_url: str | None = None
    source: str = ""
    source_url: str | None = None
    source_type: ProviderType = ProviderType.LOCAL
    effective_date: str | None = None
    last_verified: str | None = None
    status: str = "active"


class EligibilityCheck(BaseModel):
    """Result of eligibility check."""
    model_config = ConfigDict(frozen=True)

    scheme_id: str
    eligible: bool | None = None  # True/False/None (unknown)
    matched_conditions: list[dict] = Field(default_factory=list)
    unmatched_conditions: list[dict] = Field(default_factory=list)
    unknown_conditions: list[dict] = Field(default_factory=list)
    confidence: float = 0.0


class SchemeProvider(ABC):
    """Abstract base class for scheme data providers."""

    @abstractmethod
    async def get_schemes(self, filters: dict | None = None) -> list[SchemeBase]:
        """Get schemes matching filters.

        Args:
            filters: Optional filters (category, state, age, etc.)

        Returns:
            List of schemes
        """
        pass

    @abstractmethod
    async def get_scheme(self, scheme_id: str) -> SchemeBase | None:
        """Get specific scheme by ID.

        Args:
            scheme_id: Scheme identifier

        Returns:
            Scheme or None if not found
        """
        pass

    @abstractmethod
    async def check_eligibility(
        self,
        scheme_id: str,
        profile: dict
    ) -> EligibilityCheck:
        """Check eligibility for a scheme.

        Args:
            scheme_id: Scheme identifier
            profile: User profile data

        Returns:
            Eligibility check result
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is currently available."""
        pass

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return provider type."""
        pass


class LocalVerifiedProvider(SchemeProvider):
    """Local JSON-based verified schemes provider.

    Always available as fallback. Data from government_schemes.json.
    """

    def __init__(self):
        self.data_file = PROJECT_ROOT / "data" / "government_schemes.json"
        self._schemes: list[dict] | None = None
        self._load_schemes()

    def _load_schemes(self):
        """Load schemes from JSON file."""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._schemes = data.get("schemes", [])
        except FileNotFoundError:
            print(f"Schemes file not found: {self.data_file}")
            self._schemes = []
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in schemes file: {e}")
            self._schemes = []

    async def get_schemes(self, filters: dict | None = None) -> list[SchemeBase]:
        """Get local schemes with optional filters."""
        if not self._schemes:
            return []

        schemes = self._schemes

        # Apply filters
        if filters:
            if "category" in filters:
                schemes = [
                    s for s in schemes
                    if filters["category"].lower() in s.get("category", "").lower()
                ]
            if "state" in filters:
                state = filters["state"].lower()
                schemes = [
                    s for s in schemes
                    if state in str(s.get("jurisdiction", {}).get("states", [])).lower()
                    or s.get("jurisdiction", {}).get("level") == "central"
                ]

        return [self._to_scheme_base(s) for s in schemes]

    async def get_scheme(self, scheme_id: str) -> SchemeBase | None:
        """Get specific scheme by ID."""
        if not self._schemes:
            return None

        for scheme in self._schemes:
            if scheme.get("id") == scheme_id:
                return self._to_scheme_base(scheme)
        return None

    async def check_eligibility(
        self,
        scheme_id: str,
        profile: dict
    ) -> EligibilityCheck:
        """Check eligibility using deterministic rules."""
        scheme = await self.get_scheme(scheme_id)
        if not scheme:
            return EligibilityCheck(
                scheme_id=scheme_id,
                eligible=None,
                confidence=0.0,
            )

        # Use existing scheme eligibility engine
        from backend.legal.scheme_eligibility import SchemeEligibilityEngine

        engine = SchemeEligibilityEngine()
        raw_scheme = next(
            (s for s in self._schemes if s.get("id") == scheme_id),
            None
        )

        if raw_scheme:
            result = engine.evaluate_eligibility(raw_scheme, profile)
            return EligibilityCheck(
                scheme_id=scheme_id,
                eligible=result.get("eligible"),
                matched_conditions=result.get("matched", []),
                unmatched_conditions=result.get("unmatched", []),
                unknown_conditions=result.get("unknown", []),
                confidence=1.0 if result.get("eligible") is not None else 0.5,
            )

        return EligibilityCheck(scheme_id=scheme_id, eligible=None, confidence=0.0)

    def _to_scheme_base(self, raw_scheme: dict) -> SchemeBase:
        """Convert raw scheme dict to SchemeBase model."""
        return SchemeBase(
            id=raw_scheme.get("id", ""),
            name=raw_scheme.get("name", ""),
            short_name=raw_scheme.get("short_name", ""),
            description=raw_scheme.get("description", ""),
            benefit_summary=raw_scheme.get("benefit_summary", ""),
            target_group=raw_scheme.get("target_group", ""),
            jurisdiction=raw_scheme.get("jurisdiction", {}),
            eligibility=raw_scheme.get("eligibility_rules", []),
            required_documents=raw_scheme.get("required_documents", []),
            application_url=raw_scheme.get("application_url"),
            official_portal_url=raw_scheme.get("official_portal_url"),
            source=raw_scheme.get("source", ""),
            source_url=raw_scheme.get("source_url"),
            source_type=ProviderType.LOCAL,
            effective_date=raw_scheme.get("effective_date"),
            last_verified=raw_scheme.get("last_verified"),
            status=raw_scheme.get("status", "active"),
        )

    @property
    def is_available(self) -> bool:
        """Local provider is always available."""
        return self._schemes is not None and len(self._schemes) > 0

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LOCAL


class APISetuMySchemeProvider(SchemeProvider):
    """API Setu myScheme provider (OAuth 2.0).

    Requires API Setu registration and approval.
    """

    def __init__(self):
        self.client_id = os.getenv("APISETU_CLIENT_ID")
        self.client_secret = os.getenv("APISETU_CLIENT_SECRET")
        self.sandbox_mode = os.getenv("APISETU_SANDBOX", "true").lower() == "true"
        self.base_url = (
            "https://sandbox.api-setu.in" if self.sandbox_mode
            else "https://api.apisetu.gov.in"
        )
        self.oauth_token: str | None = None
        self.token_expires: datetime | None = None
        self.cache = get_cache()

    async def _get_access_token(self) -> str:
        """Get OAuth 2.0 access token."""
        if self.oauth_token and self.token_expires:
            if datetime.utcnow() < self.token_expires:
                return self.oauth_token

        # Request new token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()

            self.oauth_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self.token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)

            return self.oauth_token

    async def get_schemes(self, filters: dict | None = None) -> list[SchemeBase]:
        """Get schemes from API Setu myScheme API."""
        # Check cache first
        cache_key = json.dumps(filters or {}, sort_keys=True)
        cached = await self.cache.get_schemes(cache_key)
        if cached:
            return [SchemeBase(**s) for s in cached]

        # Fetch from API
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/myscheme/v1/schemes",
                headers=headers,
                params=filters or {},
            )
            response.raise_for_status()
            data = response.json()

            schemes = [
                self._transform_scheme(s) for s in data.get("schemes", [])
            ]

            # Cache for 24 hours
            await self.cache.set_schemes(
                cache_key,
                [s.model_dump() for s in schemes],
                ttl=86400
            )

            return schemes

    async def get_scheme(self, scheme_id: str) -> SchemeBase | None:
        """Get specific scheme from API Setu."""
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/myscheme/v1/schemes/{scheme_id}",
                headers=headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return self._transform_scheme(data)

    async def check_eligibility(
        self,
        scheme_id: str,
        profile: dict
    ) -> EligibilityCheck:
        """Check eligibility via API Setu (if endpoint exists)."""
        # Note: This depends on API Setu providing eligibility check endpoint
        # For now, fall back to local rules if scheme data is available
        scheme = await self.get_scheme(scheme_id)
        if not scheme:
            return EligibilityCheck(scheme_id=scheme_id, eligible=None, confidence=0.0)

        # API Setu may provide eligibility endpoint in future
        # For now, return unknown eligibility
        return EligibilityCheck(
            scheme_id=scheme_id,
            eligible=None,  # Unknown - API doesn't provide eligibility check yet
            confidence=0.5,
        )

    def _transform_scheme(self, api_data: dict) -> SchemeBase:
        """Transform API Setu response to SchemeBase model."""
        return SchemeBase(
            id=api_data.get("id", ""),
            name=api_data.get("name", ""),
            short_name=api_data.get("shortName", ""),
            description=api_data.get("description", ""),
            benefit_summary=api_data.get("benefits", ""),
            target_group=api_data.get("targetGroup", ""),
            jurisdiction={
                "level": api_data.get("level", ""),
                "state": api_data.get("state"),
            },
            eligibility=api_data.get("eligibility", {}),
            required_documents=api_data.get("documents", []),
            application_url=api_data.get("applicationUrl"),
            official_portal_url=api_data.get("portalUrl"),
            source="API Setu myScheme",
            source_url=f"{self.base_url}/myscheme",
            source_type=ProviderType.API_LIVE,
            effective_date=None,
            last_verified=datetime.utcnow().isoformat(),
            status="active",
        )

    @property
    def is_available(self) -> bool:
        """Check if API Setu credentials are configured."""
        return bool(self.client_id and self.client_secret)

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.API_LIVE


class SchemeProviderRouter:
    """Routes to best available scheme provider with fallback."""

    def __init__(self):
        self.providers: list[SchemeProvider] = [
            APISetuMySchemeProvider(),  # Try API first
            LocalVerifiedProvider(),    # Always-available fallback
        ]

    async def get_schemes(
        self,
        filters: dict | None = None
    ) -> tuple[list[SchemeBase], ProviderType]:
        """Get schemes from first available provider.

        Returns:
            (schemes, provider_type)
        """
        for provider in self.providers:
            if provider.is_available:
                try:
                    schemes = await provider.get_schemes(filters)
                    return schemes, provider.provider_type
                except Exception as e:
                    print(f"Provider {provider.provider_type} failed: {e}")
                    continue

        return [], ProviderType.LOCAL

    async def get_scheme(self, scheme_id: str) -> tuple[SchemeBase | None, ProviderType]:
        """Get scheme from first provider that has it."""
        for provider in self.providers:
            if provider.is_available:
                try:
                    scheme = await provider.get_scheme(scheme_id)
                    if scheme:
                        return scheme, provider.provider_type
                except Exception as e:
                    print(f"Provider {provider.provider_type} failed: {e}")
                    continue

        return None, ProviderType.LOCAL

    async def check_eligibility(
        self,
        scheme_id: str,
        profile: dict
    ) -> tuple[EligibilityCheck, ProviderType]:
        """Check eligibility using first provider that supports it."""
        # For now, use local provider for eligibility (has deterministic rules)
        local_provider = next(
            (p for p in self.providers if isinstance(p, LocalVerifiedProvider)),
            None
        )

        if local_provider and local_provider.is_available:
            result = await local_provider.check_eligibility(scheme_id, profile)
            return result, ProviderType.LOCAL

        return EligibilityCheck(scheme_id=scheme_id, eligible=None, confidence=0.0), ProviderType.LOCAL


@lru_cache(maxsize=1)
def get_scheme_router() -> SchemeProviderRouter:
    """Get singleton scheme router instance."""
    return SchemeProviderRouter()
