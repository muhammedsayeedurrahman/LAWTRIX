"""Automation state machine for workflow execution.

Explicit state machine with persistent transitions for resumable automation.
Handles human checkpoints, failures, and recovery.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AutomationStateEnum(str, Enum):
    """Automation execution states."""
    # Initial states
    DISCOVERED = "discovered"  # Workflow identified but not started
    PREPARED = "prepared"  # Draft/documents prepared
    VALIDATED = "validated"  # Prerequisites checked
    READY_FOR_USER_REVIEW = "ready_for_user_review"  # Awaiting user review
    USER_CONFIRMED = "user_confirmed"  # User approved action

    # Execution states
    NAVIGATING = "navigating"  # Navigating to portal
    WAITING_FOR_LOGIN = "waiting_for_login"  # User must log in
    WAITING_FOR_OTP = "waiting_for_otp"  # User must enter OTP
    WAITING_FOR_CAPTCHA = "waiting_for_captcha"  # User must solve CAPTCHA
    WAITING_FOR_PAYMENT = "waiting_for_payment"  # User must complete payment
    FILLING = "filling"  # Filling form fields
    READY_TO_SUBMIT = "ready_to_submit"  # Form filled, ready for final confirmation
    FINAL_CONFIRMATION_REQUIRED = "final_confirmation_required"  # User must confirm submission
    SUBMITTING = "submitting"  # Submitting form

    # Terminal states
    SUBMITTED = "submitted"  # Successfully submitted
    SUBMISSION_FAILED = "submission_failed"  # Submission failed
    TRACKING = "tracking"  # Monitoring status


class CheckpointType(str, Enum):
    """Types of human checkpoints."""
    LOGIN = "login"
    OTP = "otp"
    CAPTCHA = "captcha"
    PAYMENT = "payment"
    REVIEW = "review"
    CONFIRMATION = "confirmation"


class StateTransitionReason(str, Enum):
    """Reasons for state transitions."""
    USER_ACTION = "user_action"
    SYSTEM_ACTION = "system_action"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    CHECKPOINT_REQUIRED = "checkpoint_required"
    CHECKPOINT_COMPLETED = "checkpoint_completed"
    ERROR = "error"
    TIMEOUT = "timeout"
    MANUAL = "manual"


class StateTransition(BaseModel):
    """Single state transition record."""
    model_config = ConfigDict(frozen=True)

    from_state: AutomationStateEnum
    to_state: AutomationStateEnum
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reason: StateTransitionReason
    details: str | None = Field(None, description="Additional details about transition")
    user_id: str | None = Field(None, description="User who triggered transition if applicable")
    error_message: str | None = Field(None, description="Error message if transition due to error")


class HumanCheckpoint(BaseModel):
    """Human intervention checkpoint."""
    model_config = ConfigDict(frozen=True)

    checkpoint_id: str = Field(..., description="Unique checkpoint identifier")
    checkpoint_type: CheckpointType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    state: AutomationStateEnum = Field(..., description="State that triggered this checkpoint")

    # User messaging
    title: str = Field(..., description="What is happening")
    reason: str = Field(..., description="Why it is needed")
    user_action_required: str = Field(..., description="What user must do")
    what_happens_next: str = Field(..., description="What happens after checkpoint")

    # Resume information
    can_resume: bool = Field(default=True, description="Whether automation can resume after checkpoint")
    resume_state: AutomationStateEnum | None = Field(None, description="State to resume to after checkpoint")

    # Checkpoint data (for OTP, CAPTCHA, etc.)
    data: dict = Field(default_factory=dict, description="Checkpoint-specific data")


class AutomationSession(BaseModel):
    """Automation session state.

    Represents the current state of workflow automation execution.
    Persisted to database for crash recovery and resumability.
    """
    model_config = ConfigDict(frozen=True)

    session_id: str = Field(..., description="Unique session identifier")
    case_id: str = Field(..., description="Associated case ID")
    workflow_name: str = Field(..., description="Workflow being automated")

    # Current state
    current_state: AutomationStateEnum
    previous_state: AutomationStateEnum | None = None

    # State history
    transitions: list[StateTransition] = Field(default_factory=list)

    # Checkpoints
    current_checkpoint: HumanCheckpoint | None = None
    completed_checkpoints: list[HumanCheckpoint] = Field(default_factory=list)

    # Session metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    # Portal session data (for resumability)
    portal_url: str | None = None
    portal_session_data: dict = Field(default_factory=dict, description="Portal-specific session data")

    # Form data
    form_id: str | None = None
    filled_fields: dict = Field(default_factory=dict, description="Fields already filled")

    # Error handling
    error_count: int = Field(default=0, description="Number of errors encountered")
    last_error: str | None = None


class AutomationStateMachine:
    """State machine for workflow automation.

    Manages state transitions, checkpoints, and resumability.
    """

    # Valid state transitions
    TRANSITIONS = {
        AutomationStateEnum.DISCOVERED: [
            AutomationStateEnum.PREPARED,
        ],
        AutomationStateEnum.PREPARED: [
            AutomationStateEnum.VALIDATED,
            AutomationStateEnum.READY_FOR_USER_REVIEW,
        ],
        AutomationStateEnum.VALIDATED: [
            AutomationStateEnum.READY_FOR_USER_REVIEW,
        ],
        AutomationStateEnum.READY_FOR_USER_REVIEW: [
            AutomationStateEnum.USER_CONFIRMED,
            AutomationStateEnum.PREPARED,  # User wants to edit
        ],
        AutomationStateEnum.USER_CONFIRMED: [
            AutomationStateEnum.NAVIGATING,
        ],
        AutomationStateEnum.NAVIGATING: [
            AutomationStateEnum.WAITING_FOR_LOGIN,
            AutomationStateEnum.FILLING,
            AutomationStateEnum.SUBMISSION_FAILED,
        ],
        AutomationStateEnum.WAITING_FOR_LOGIN: [
            AutomationStateEnum.FILLING,
            AutomationStateEnum.SUBMISSION_FAILED,
        ],
        AutomationStateEnum.FILLING: [
            AutomationStateEnum.WAITING_FOR_OTP,
            AutomationStateEnum.WAITING_FOR_CAPTCHA,
            AutomationStateEnum.READY_TO_SUBMIT,
            AutomationStateEnum.SUBMISSION_FAILED,
        ],
        AutomationStateEnum.WAITING_FOR_OTP: [
            AutomationStateEnum.FILLING,
            AutomationStateEnum.READY_TO_SUBMIT,
            AutomationStateEnum.SUBMISSION_FAILED,
        ],
        AutomationStateEnum.WAITING_FOR_CAPTCHA: [
            AutomationStateEnum.FILLING,
            AutomationStateEnum.READY_TO_SUBMIT,
            AutomationStateEnum.SUBMISSION_FAILED,
        ],
        AutomationStateEnum.READY_TO_SUBMIT: [
            AutomationStateEnum.FINAL_CONFIRMATION_REQUIRED,
        ],
        AutomationStateEnum.FINAL_CONFIRMATION_REQUIRED: [
            AutomationStateEnum.SUBMITTING,
            AutomationStateEnum.FILLING,  # User wants to edit
        ],
        AutomationStateEnum.SUBMITTING: [
            AutomationStateEnum.SUBMITTED,
            AutomationStateEnum.SUBMISSION_FAILED,
        ],
        AutomationStateEnum.SUBMITTED: [
            AutomationStateEnum.TRACKING,
        ],
        AutomationStateEnum.SUBMISSION_FAILED: [
            AutomationStateEnum.FILLING,  # Retry
            AutomationStateEnum.READY_FOR_USER_REVIEW,  # Review and retry
        ],
        AutomationStateEnum.TRACKING: [],  # Terminal state
        AutomationStateEnum.WAITING_FOR_PAYMENT: [
            AutomationStateEnum.FILLING,
            AutomationStateEnum.SUBMISSION_FAILED,
        ],
    }

    # Checkpoint states (states that require human intervention)
    CHECKPOINT_STATES = {
        AutomationStateEnum.WAITING_FOR_LOGIN,
        AutomationStateEnum.WAITING_FOR_OTP,
        AutomationStateEnum.WAITING_FOR_CAPTCHA,
        AutomationStateEnum.WAITING_FOR_PAYMENT,
        AutomationStateEnum.READY_FOR_USER_REVIEW,
        AutomationStateEnum.FINAL_CONFIRMATION_REQUIRED,
    }

    def __init__(self, session: AutomationSession):
        self.session = session

    def can_transition(self, to_state: AutomationStateEnum) -> bool:
        """Check if transition to new state is valid."""
        allowed_transitions = self.TRANSITIONS.get(self.session.current_state, [])
        return to_state in allowed_transitions

    def transition(
        self,
        to_state: AutomationStateEnum,
        reason: StateTransitionReason,
        details: str | None = None,
        user_id: str | None = None,
        error_message: str | None = None,
    ) -> AutomationSession:
        """Transition to new state.

        Returns:
            New AutomationSession with updated state

        Raises:
            ValueError: If transition is not valid
        """
        if not self.can_transition(to_state):
            raise ValueError(
                f"Invalid transition from {self.session.current_state} to {to_state}. "
                f"Allowed: {self.TRANSITIONS.get(self.session.current_state, [])}"
            )

        transition = StateTransition(
            from_state=self.session.current_state,
            to_state=to_state,
            reason=reason,
            details=details,
            user_id=user_id,
            error_message=error_message,
        )

        new_transitions = list(self.session.transitions) + [transition]

        return self.session.model_copy(
            update={
                "previous_state": self.session.current_state,
                "current_state": to_state,
                "transitions": new_transitions,
                "updated_at": datetime.utcnow(),
            }
        )

    def create_checkpoint(
        self,
        checkpoint_type: CheckpointType,
        title: str,
        reason: str,
        user_action_required: str,
        what_happens_next: str,
        resume_state: AutomationStateEnum | None = None,
        data: dict | None = None,
    ) -> AutomationSession:
        """Create a human checkpoint.

        Returns:
            New AutomationSession with checkpoint
        """
        checkpoint_id = f"{self.session.session_id}_{checkpoint_type.value}_{datetime.utcnow().timestamp()}"

        checkpoint = HumanCheckpoint(
            checkpoint_id=checkpoint_id,
            checkpoint_type=checkpoint_type,
            state=self.session.current_state,
            title=title,
            reason=reason,
            user_action_required=user_action_required,
            what_happens_next=what_happens_next,
            resume_state=resume_state,
            data=data or {},
        )

        return self.session.model_copy(
            update={
                "current_checkpoint": checkpoint,
                "updated_at": datetime.utcnow(),
            }
        )

    def complete_checkpoint(self) -> AutomationSession:
        """Mark current checkpoint as completed.

        Returns:
            New AutomationSession with checkpoint completed
        """
        if not self.session.current_checkpoint:
            raise ValueError("No active checkpoint to complete")

        completed_checkpoint = self.session.current_checkpoint.model_copy(
            update={"completed_at": datetime.utcnow()}
        )

        new_completed = list(self.session.completed_checkpoints) + [completed_checkpoint]

        return self.session.model_copy(
            update={
                "current_checkpoint": None,
                "completed_checkpoints": new_completed,
                "updated_at": datetime.utcnow(),
            }
        )

    def is_checkpoint_state(self) -> bool:
        """Check if current state requires human checkpoint."""
        return self.session.current_state in self.CHECKPOINT_STATES

    def record_error(self, error_message: str) -> AutomationSession:
        """Record an error.

        Returns:
            New AutomationSession with error recorded
        """
        return self.session.model_copy(
            update={
                "error_count": self.session.error_count + 1,
                "last_error": error_message,
                "updated_at": datetime.utcnow(),
            }
        )

    def get_state_history(self) -> list[dict]:
        """Get human-readable state history.

        Returns:
            List of state transition dicts
        """
        return [
            {
                "from": t.from_state.value,
                "to": t.to_state.value,
                "timestamp": t.timestamp.isoformat(),
                "reason": t.reason.value,
                "details": t.details,
            }
            for t in self.session.transitions
        ]

    def can_resume(self) -> bool:
        """Check if automation can be resumed from current state.

        Returns:
            True if automation can continue
        """
        # Cannot resume from terminal failure state without going back to review
        if self.session.current_state == AutomationStateEnum.SUBMISSION_FAILED:
            return False

        # Cannot resume if too many errors
        if self.session.error_count > 3:
            return False

        return True
