"""Unified CitizenCase model — core abstraction spanning all civic/legal workflows.

This model provides a single source of truth for case state across RTI, CPGRAMS,
schemes, consumer, tenant, labour, and legal workflows.

All models are immutable (frozen) for safety and audit trail integrity.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class IntentCategory(str, Enum):
    """Primary intent categories for routing."""
    INFORMATION_REQUEST = "information_request"  # RTI
    GOVERNMENT_SERVICE_GRIEVANCE = "government_service_grievance"  # CPGRAMS
    SCHEME_ELIGIBILITY = "scheme_eligibility"  # Schemes
    RIGHTS_GUIDANCE_CONSUMER = "rights_guidance_consumer"  # Consumer
    RIGHTS_GUIDANCE_TENANT = "rights_guidance_tenant"  # Tenant
    RIGHTS_GUIDANCE_LABOUR = "rights_guidance_labour"  # Labour
    CRIMINAL_LEGAL_INCIDENT = "criminal_legal_incident"  # Legal/criminal
    GENERAL_CIVIC_INFORMATION = "general_civic_information"  # Guidance


class WorkflowStatus(str, Enum):
    """Workflow lifecycle status."""
    INITIATED = "initiated"
    COLLECTING_INFO = "collecting_info"
    READY_FOR_REVIEW = "ready_for_review"
    USER_REVIEWING = "user_reviewing"
    READY_FOR_ACTION = "ready_for_action"
    AUTOMATION_IN_PROGRESS = "automation_in_progress"
    AWAITING_USER_INPUT = "awaiting_user_input"
    SUBMITTED = "submitted"
    TRACKING = "tracking"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ActionType(str, Enum):
    """Type of action to be performed."""
    RTI_APPLICATION = "rti_application"
    CPGRAMS_GRIEVANCE = "cpgrams_grievance"
    CONSUMER_COMPLAINT = "consumer_complaint"
    RENT_CONTROL_COMPLAINT = "rent_control_complaint"
    LABOUR_COMPLAINT = "labour_complaint"
    SCHEME_APPLICATION = "scheme_application"
    LEGAL_NOTICE = "legal_notice"
    FIR_FILING = "fir_filing"


class AutomationMode(str, Enum):
    """How the action will be executed."""
    API = "api"  # Direct API integration
    BROWSER = "browser"  # Browser automation (OpenClaw)
    GUIDED = "guided"  # User-assisted with guidance
    MANUAL = "manual"  # Fully manual (provide instructions only)


class AutomationStateEnum(str, Enum):
    """Current state in automation flow."""
    NOT_STARTED = "not_started"
    DISCOVERING = "discovering"
    PREPARING = "preparing"
    VALIDATED = "validated"
    READY_FOR_USER_REVIEW = "ready_for_user_review"
    USER_CONFIRMED = "user_confirmed"
    NAVIGATING = "navigating"
    WAITING_FOR_LOGIN = "waiting_for_login"
    WAITING_FOR_OTP = "waiting_for_otp"
    WAITING_FOR_CAPTCHA = "waiting_for_captcha"
    WAITING_FOR_PAYMENT = "waiting_for_payment"
    FILLING = "filling"
    READY_TO_SUBMIT = "ready_to_submit"
    FINAL_CONFIRMATION_REQUIRED = "final_confirmation_required"
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"
    SUBMISSION_FAILED = "submission_failed"
    TRACKING = "tracking"


class SubmissionStatus(str, Enum):
    """Status of submission to external authority."""
    NOT_SUBMITTED = "not_submitted"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    APPEAL_PENDING = "appeal_pending"


class EventType(str, Enum):
    """Timeline event types."""
    CREATED = "created"
    INTENT_CLASSIFIED = "intent_classified"
    WORKFLOW_STARTED = "workflow_started"
    INFORMATION_COLLECTED = "information_collected"
    DRAFT_GENERATED = "draft_generated"
    USER_REVIEWED = "user_reviewed"
    USER_CONFIRMED = "user_confirmed"
    AUTOMATION_STARTED = "automation_started"
    CHECKPOINT_PAUSED = "checkpoint_paused"
    CHECKPOINT_RESUMED = "checkpoint_resumed"
    SUBMITTED = "submitted"
    STATUS_CHANGED = "status_changed"
    REMINDER_SENT = "reminder_sent"
    COMPLETED = "completed"


# ── Nested Models ────────────────────────────────────────────────────────────

class Attachment(BaseModel):
    """Uploaded file attachment."""
    model_config = ConfigDict(frozen=True)

    attachment_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    storage_key: str | None = None  # S3 key or file path


class CaseInput(BaseModel):
    """Raw user input to the system."""
    model_config = ConfigDict(frozen=True)

    raw_text: str
    transcript: str | None = None  # From voice input
    language: str = "en-IN"
    attachments: list[Attachment] = Field(default_factory=list)
    input_method: str = "text"  # text|voice|document|image


class CaseIntent(BaseModel):
    """Classified user intent."""
    model_config = ConfigDict(frozen=True)

    category: IntentCategory
    subcategory: str = ""
    confidence: float = 0.0  # 0.0 to 1.0
    reasoning: str = ""
    auto_handoff_eligible: bool = False  # True if confidence >= 0.75


class Fact(BaseModel):
    """Extracted fact from user input or documents."""
    model_config = ConfigDict(frozen=True)

    fact_type: str  # e.g., "monthly_rent", "employer_name", "incident_date"
    value: str
    source: str  # "user_input"|"document"|"extracted"
    confidence: float = 1.0
    verified: bool = False


class CaseProblem(BaseModel):
    """User's problem description."""
    model_config = ConfigDict(frozen=True)

    summary: str  # One-sentence summary
    facts: list[Fact] = Field(default_factory=list)
    facts_narrative: str = ""  # Detailed description
    requested_outcome: str = ""  # What user wants to achieve


class CitizenProfile(BaseModel):
    """User demographics and profile."""
    model_config = ConfigDict(frozen=True)

    name: str | None = None
    age: int | None = None
    occupation: str | None = None
    monthly_income: float | None = None
    is_income_tax_payer: bool | None = None
    # Social/economic indicators for scheme eligibility
    is_unorganised_worker: bool | None = None
    covered_by_epfo: bool | None = None
    covered_by_esic: bool | None = None
    covered_by_nps: bool | None = None
    # Add more fields as needed for schemes


class Jurisdiction(BaseModel):
    """Geographic and authority jurisdiction."""
    model_config = ConfigDict(frozen=True)

    state: str | None = None
    district: str | None = None
    city: str | None = None
    locality: str | None = None
    pincode: str | None = None
    authority: str | None = None  # Identified authority/department
    authority_confidence: float = 0.0
    authority_verified: bool = False
    filing_channel: str | None = None  # "central"|"state"|"district"|"online"|"offline"


class WorkflowState(BaseModel):
    """Current workflow execution state."""
    model_config = ConfigDict(frozen=True)

    name: str  # rti|cpgrams|schemes|consumer|tenant|labour|legal
    status: WorkflowStatus = WorkflowStatus.INITIATED
    current_step: str = ""
    required_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class Document(BaseModel):
    """Document (generated or user-provided)."""
    model_config = ConfigDict(frozen=True)

    doc_id: str = Field(default_factory=lambda: str(uuid4()))
    doc_type: str  # e.g., "rti_draft", "grievance", "rent_agreement", "salary_slip"
    title: str
    content: str | None = None  # Text content
    storage_key: str | None = None  # For binary files
    generated_at: datetime | None = None
    source: str = "user"  # "user"|"system"|"digilocker"
    verified: bool = False


class CaseEvidence(BaseModel):
    """Evidence and supporting documents."""
    model_config = ConfigDict(frozen=True)

    documents: list[Document] = Field(default_factory=list)
    extracted_facts: list[Fact] = Field(default_factory=list)
    source_documents: list[str] = Field(default_factory=list)  # Doc IDs


class CaseDocuments(BaseModel):
    """All case documents."""
    model_config = ConfigDict(frozen=True)

    generated: list[Document] = Field(default_factory=list)
    user_provided: list[Document] = Field(default_factory=list)


class CaseAction(BaseModel):
    """Planned action."""
    model_config = ConfigDict(frozen=True)

    action_type: ActionType | None = None
    target_authority: str | None = None
    target_portal: str | None = None  # Portal ID for browser automation
    target_api: str | None = None  # API endpoint for API automation
    action_summary: str = ""


class AutomationState(BaseModel):
    """Automation execution state."""
    model_config = ConfigDict(frozen=True)

    mode: AutomationMode = AutomationMode.MANUAL
    capability: str | None = None  # What automation is available
    current_state: AutomationStateEnum = AutomationStateEnum.NOT_STARTED
    blocked_reason: str | None = None
    pending_user_action: str | None = None
    session_id: str | None = None  # OpenClaw session ID


class CaseConsent(BaseModel):
    """User consent for various operations."""
    model_config = ConfigDict(frozen=True)

    data_sharing: bool = False
    document_access: bool = False
    automation: bool = False
    final_submission: bool = False
    digilocker_access: bool = False
    granted_at: datetime | None = None


class SubmissionState(BaseModel):
    """External submission status."""
    model_config = ConfigDict(frozen=True)

    status: SubmissionStatus = SubmissionStatus.NOT_SUBMITTED
    reference_id: str | None = None  # CPGRAMS reg #, RTI application #
    submitted_at: datetime | None = None
    authority: str | None = None
    portal: str | None = None
    confirmation_evidence: str | None = None  # Screenshot, email, etc.


class Reminder(BaseModel):
    """Scheduled reminder."""
    model_config = ConfigDict(frozen=True)

    reminder_id: str = Field(default_factory=lambda: str(uuid4()))
    scheduled_for: datetime
    message: str
    sent: bool = False


class StatusChange(BaseModel):
    """Status change history."""
    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    old_status: str
    new_status: str
    source: str  # "system"|"portal"|"user"
    details: dict[str, Any] = Field(default_factory=dict)


class TrackingState(BaseModel):
    """Case tracking and follow-up."""
    model_config = ConfigDict(frozen=True)

    next_check: datetime | None = None
    reminders: list[Reminder] = Field(default_factory=list)
    status_history: list[StatusChange] = Field(default_factory=list)
    last_checked: datetime | None = None
    tracking_source: str | None = None  # API endpoint or portal URL


class Provenance(BaseModel):
    """Data source and verification."""
    model_config = ConfigDict(frozen=True)

    source: str  # "user_input"|"system_generated"|"api"|"digilocker"|"ocr"
    source_url: str | None = None
    verified_at: datetime | None = None
    confidence: float = 1.0


class TimelineEvent(BaseModel):
    """Timeline event."""
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: EventType
    actor: str  # "system"|"user"|"authority"
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


# ── Main CitizenCase Model ───────────────────────────────────────────────────

class CitizenCase(BaseModel):
    """Unified case state spanning all civic/legal workflows.

    This is the core abstraction that provides a single source of truth
    for case data across RTI, CPGRAMS, schemes, consumer, tenant, labour,
    and legal workflows.

    All nested models are immutable (frozen) for safety and audit integrity.
    """
    model_config = ConfigDict(frozen=True)

    # Identity
    case_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    citizen_id: str | None = None  # Foreign key to citizens table

    # Input
    input: CaseInput

    # Intent
    intent: CaseIntent

    # Problem
    problem: CaseProblem

    # Profile
    profile: CitizenProfile = Field(default_factory=CitizenProfile)

    # Jurisdiction
    jurisdiction: Jurisdiction = Field(default_factory=Jurisdiction)

    # Workflow
    workflow: WorkflowState

    # Evidence
    evidence: CaseEvidence = Field(default_factory=CaseEvidence)

    # Documents
    documents: CaseDocuments = Field(default_factory=CaseDocuments)

    # Action
    action: CaseAction = Field(default_factory=CaseAction)

    # Automation
    automation: AutomationState = Field(default_factory=AutomationState)

    # Consent
    consent: CaseConsent = Field(default_factory=CaseConsent)

    # Submission
    submission: SubmissionState = Field(default_factory=SubmissionState)

    # Tracking
    tracking: TrackingState = Field(default_factory=TrackingState)

    # Provenance
    provenance: Provenance

    def with_updates(self, **kwargs) -> CitizenCase:
        """Create a new CitizenCase with updated fields (immutable pattern).

        Example:
            updated_case = case.with_updates(
                workflow=WorkflowState(name="rti", status=WorkflowStatus.READY_FOR_REVIEW),
                updated_at=datetime.utcnow()
            )
        """
        return self.model_copy(update=kwargs)

    def to_timeline_event(
        self,
        event_type: EventType,
        actor: str,
        description: str,
        details: dict[str, Any] | None = None
    ) -> TimelineEvent:
        """Create a timeline event for this case."""
        return TimelineEvent(
            event_type=event_type,
            actor=actor,
            description=description,
            details=details or {},
        )


# ── Helper Functions ──────────────────────────────────────────────────────────

def create_case_from_input(
    raw_text: str,
    language: str = "en-IN",
    input_method: str = "text",
) -> CitizenCase:
    """Create a new CitizenCase from raw user input."""
    return CitizenCase(
        input=CaseInput(
            raw_text=raw_text,
            language=language,
            input_method=input_method,
        ),
        intent=CaseIntent(
            category=IntentCategory.GENERAL_CIVIC_INFORMATION,  # Will be classified
            confidence=0.0,
        ),
        problem=CaseProblem(summary=""),
        workflow=WorkflowState(name="classification"),
        provenance=Provenance(source="user_input"),
    )


def update_case_intent(
    case: CitizenCase,
    category: IntentCategory,
    confidence: float,
    reasoning: str,
    subcategory: str = "",
) -> CitizenCase:
    """Update case with classified intent."""
    return case.with_updates(
        intent=CaseIntent(
            category=category,
            subcategory=subcategory,
            confidence=confidence,
            reasoning=reasoning,
            auto_handoff_eligible=confidence >= 0.75,
        ),
        updated_at=datetime.utcnow(),
    )


def update_case_workflow(
    case: CitizenCase,
    workflow_name: str,
    status: WorkflowStatus = WorkflowStatus.COLLECTING_INFO,
) -> CitizenCase:
    """Transition case to a specific workflow."""
    return case.with_updates(
        workflow=WorkflowState(
            name=workflow_name,
            status=status,
        ),
        updated_at=datetime.utcnow(),
    )
