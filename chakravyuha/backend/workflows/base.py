"""Base workflow handler contract.

All workflows (RTI, CPGRAMS, Consumer, Tenant, Labour, etc.) implement
this standard interface for consistency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.models.citizen_case import CitizenCase


class ExecutionStatus(str, Enum):
    """Status of workflow execution."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING_USER_ACTION = "pending_user_action"
    AUTOMATION_IN_PROGRESS = "automation_in_progress"


class PrepareResult(BaseModel):
    """Result of workflow preparation."""
    model_config = ConfigDict(frozen=True)

    required_fields: list[str] = Field(default_factory=list)
    known_fields: dict[str, any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    authority: str | None = None
    draft: str | None = None  # Generated draft document
    action_options: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Result of workflow validation."""
    model_config = ConfigDict(frozen=True)

    ready: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ActionPreview(BaseModel):
    """Preview of action to be taken."""
    model_config = ConfigDict(frozen=True)

    target_authority: str
    action_type: str  # "RTI Application", "Consumer Complaint", etc.
    documents_to_submit: list[str] = Field(default_factory=list)
    data_shared: dict[str, any] = Field(default_factory=dict)
    fees: str | None = None
    expected_outcome: str = ""
    risks_warnings: list[str] = Field(default_factory=list)
    what_happens_next: str = ""
    blockers: list[str] = Field(default_factory=list)  # If action can't proceed
    next_steps: list[str] = Field(default_factory=list)  # User actions needed


class ExecutionResult(BaseModel):
    """Result of workflow execution."""
    model_config = ConfigDict(frozen=True)

    status: ExecutionStatus
    reference_id: str | None = None
    message: str = ""
    next_steps: list[str] = Field(default_factory=list)
    error: str | None = None


class TrackingResult(BaseModel):
    """Result of status tracking."""
    model_config = ConfigDict(frozen=True)

    current_status: str
    last_updated: datetime
    next_check: datetime | None = None
    status_history: list[dict] = Field(default_factory=list)
    tracking_source: str | None = None  # API endpoint or portal URL


class WorkflowHandler(ABC):
    """Abstract base class for all workflow handlers.

    Every workflow (RTI, CPGRAMS, Consumer, Tenant, Labour, etc.) must
    implement this interface for consistency.
    """

    @property
    @abstractmethod
    def workflow_name(self) -> str:
        """Return workflow name (e.g., 'rti', 'consumer', 'tenant')."""
        pass

    @abstractmethod
    async def prepare(self, case: CitizenCase) -> PrepareResult:
        """Analyze case and prepare workflow.

        This method:
        1. Extracts required information from case
        2. Identifies missing fields
        3. Determines target authority
        4. Generates draft documents (if possible)
        5. Provides action options

        Args:
            case: Current CitizenCase

        Returns:
            PrepareResult with required/known/missing fields, draft, etc.
        """
        pass

    @abstractmethod
    async def validate(self, case: CitizenCase) -> ValidationResult:
        """Validate if case is ready for action.

        Checks:
        - All required fields present
        - Data is valid and consistent
        - No blockers preventing action

        Args:
            case: Current CitizenCase

        Returns:
            ValidationResult with ready status and blockers
        """
        pass

    @abstractmethod
    async def preview_action(self, case: CitizenCase) -> ActionPreview:
        """Generate human-readable preview of action.

        Shows user exactly what will happen:
        - What authority will receive the action
        - What data will be shared
        - What documents will be submitted
        - Expected outcome and next steps

        Args:
            case: Current CitizenCase

        Returns:
            ActionPreview with all details
        """
        pass

    @abstractmethod
    def requires_confirmation(self, case: CitizenCase) -> bool:
        """Check if explicit user confirmation is needed.

        Returns:
            True if user must confirm before execution
        """
        pass

    @abstractmethod
    async def execute(self, case: CitizenCase) -> ExecutionResult:
        """Execute the workflow action.

        This method should:
        1. Verify user confirmation received
        2. Validate all prerequisites
        3. Execute via API/browser/guided mode
        4. Handle human checkpoints (OTP, CAPTCHA, etc.)
        5. Store reference ID on success

        Only call if requires_confirmation() returned True and user confirmed.

        Args:
            case: Current CitizenCase

        Returns:
            ExecutionResult with status and reference_id
        """
        pass

    @abstractmethod
    async def track(self, case: CitizenCase) -> TrackingResult:
        """Track status of submitted action.

        Polls external portal/API for status updates.

        Args:
            case: Current CitizenCase with submission data

        Returns:
            TrackingResult with current status
        """
        pass

    # Optional helper methods (can be overridden)

    async def collect_missing_info(
        self,
        case: CitizenCase,
        missing_fields: list[str]
    ) -> dict[str, str]:
        """Generate questions to collect missing information.

        Default implementation generates generic questions.
        Workflows can override for custom question flow.

        Args:
            case: Current CitizenCase
            missing_fields: List of missing field names

        Returns:
            Dict mapping field names to questions
        """
        questions = {}
        for field in missing_fields:
            questions[field] = f"Please provide: {field.replace('_', ' ').title()}"
        return questions

    async def extract_facts_from_narrative(
        self,
        narrative: str
    ) -> dict[str, any]:
        """Extract structured facts from free-text narrative.

        Default implementation returns empty dict.
        Workflows should override to extract domain-specific facts.

        Args:
            narrative: User's problem description

        Returns:
            Dict of extracted facts
        """
        return {}
