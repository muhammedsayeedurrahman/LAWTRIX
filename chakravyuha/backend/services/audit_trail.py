"""Comprehensive audit trail system for all case operations.

Records every action, decision, and state change for transparency and debugging.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Case lifecycle
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    CASE_DELETED = "case_deleted"

    # Intent and routing
    INTENT_CLASSIFIED = "intent_classified"
    WORKFLOW_ROUTED = "workflow_routed"
    AUTHORITY_DETERMINED = "authority_determined"

    # Data extraction
    FACTS_EXTRACTED = "facts_extracted"
    USER_CORRECTED = "user_corrected"
    DOCUMENT_PROCESSED = "document_processed"

    # Workflow progression
    DRAFT_GENERATED = "draft_generated"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    USER_REVIEWED = "user_reviewed"
    USER_CONFIRMED = "user_confirmed"

    # Automation
    AUTOMATION_STARTED = "automation_started"
    AUTOMATION_PAUSED = "automation_paused"
    AUTOMATION_RESUMED = "automation_resumed"
    CHECKPOINT_REACHED = "checkpoint_reached"
    CHECKPOINT_COMPLETED = "checkpoint_completed"

    # Submission
    SUBMISSION_ATTEMPTED = "submission_attempted"
    SUBMISSION_SUCCEEDED = "submission_succeeded"
    SUBMISSION_FAILED = "submission_failed"
    REFERENCE_ID_RECEIVED = "reference_id_received"

    # Status tracking
    STATUS_CHECKED = "status_checked"
    STATUS_CHANGED = "status_changed"
    REMINDER_SCHEDULED = "reminder_scheduled"
    REMINDER_SENT = "reminder_sent"

    # Document operations
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_ACCESSED = "document_accessed"
    DOCUMENT_SHARED = "document_shared"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"

    # System operations
    ERROR_OCCURRED = "error_occurred"
    CONFIGURATION_CHANGED = "configuration_changed"


class AuditSeverity(str, Enum):
    """Severity level of audit event."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Single audit trail event."""
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Event classification
    event_type: AuditEventType
    severity: AuditSeverity = Field(default=AuditSeverity.INFO)

    # Context
    case_id: str | None = None
    workflow_name: str | None = None
    user_id: str | None = None

    # Event details
    title: str = Field(..., description="Human-readable event title")
    description: str | None = Field(None, description="Detailed description")

    # Actor information
    actor: str | None = Field(None, description="Who/what performed this action")
    actor_type: str | None = Field(None, description="Type of actor (user, system, automation)")

    # Data changes
    before_state: dict[str, Any] | None = Field(None, description="State before change")
    after_state: dict[str, Any] | None = Field(None, description="State after change")
    changes: dict[str, Any] | None = Field(None, description="Specific changes made")

    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Error information (if applicable)
    error_message: str | None = None
    error_stack_trace: str | None = None

    # Source information
    source_component: str | None = Field(None, description="Component that generated event")
    source_function: str | None = Field(None, description="Function that generated event")


class AuditTrail:
    """Audit trail manager for recording and querying events."""

    def __init__(self):
        # In production, use database storage
        self._events: list[AuditEvent] = []

    async def record_event(
        self,
        event_type: AuditEventType,
        title: str,
        description: str | None = None,
        case_id: str | None = None,
        workflow_name: str | None = None,
        user_id: str | None = None,
        actor: str | None = None,
        actor_type: str | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        error_message: str | None = None,
        error_stack_trace: str | None = None,
        source_component: str | None = None,
        source_function: str | None = None,
    ) -> AuditEvent:
        """Record an audit event.

        Args:
            event_type: Type of event
            title: Human-readable title
            description: Detailed description
            case_id: Associated case ID
            workflow_name: Workflow name
            user_id: User ID
            actor: Who/what performed action
            actor_type: Type of actor
            severity: Event severity
            before_state: State before change
            after_state: State after change
            changes: Specific changes
            metadata: Additional metadata
            error_message: Error message if applicable
            error_stack_trace: Error stack trace
            source_component: Source component
            source_function: Source function

        Returns:
            Created AuditEvent
        """
        import uuid

        event = AuditEvent(
            event_id=f"audit_{uuid.uuid4()}",
            event_type=event_type,
            title=title,
            description=description,
            case_id=case_id,
            workflow_name=workflow_name,
            user_id=user_id,
            actor=actor,
            actor_type=actor_type,
            severity=severity,
            before_state=before_state,
            after_state=after_state,
            changes=changes,
            metadata=metadata or {},
            error_message=error_message,
            error_stack_trace=error_stack_trace,
            source_component=source_component,
            source_function=source_function,
        )

        self._events.append(event)
        return event

    async def get_case_audit_trail(
        self,
        case_id: str,
        event_types: list[AuditEventType] | None = None,
        severity: AuditSeverity | None = None,
        limit: int | None = None,
    ) -> list[AuditEvent]:
        """Get audit trail for a case.

        Args:
            case_id: Case identifier
            event_types: Filter by event types
            severity: Filter by severity
            limit: Maximum events to return

        Returns:
            List of AuditEvent
        """
        events = [e for e in self._events if e.case_id == case_id]

        if event_types:
            events = [e for e in events if e.event_type in event_types]

        if severity:
            events = [e for e in events if e.severity == severity]

        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        if limit:
            events = events[:limit]

        return events

    async def get_user_audit_trail(
        self,
        user_id: str,
        event_types: list[AuditEventType] | None = None,
        limit: int | None = None,
    ) -> list[AuditEvent]:
        """Get audit trail for a user.

        Args:
            user_id: User identifier
            event_types: Filter by event types
            limit: Maximum events to return

        Returns:
            List of AuditEvent
        """
        events = [e for e in self._events if e.user_id == user_id]

        if event_types:
            events = [e for e in events if e.event_type in event_types]

        events.sort(key=lambda e: e.timestamp, reverse=True)

        if limit:
            events = events[:limit]

        return events

    async def get_errors(
        self,
        case_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get error events.

        Args:
            case_id: Optional case filter
            limit: Maximum events to return

        Returns:
            List of error AuditEvent
        """
        events = [
            e for e in self._events
            if e.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]
        ]

        if case_id:
            events = [e for e in events if e.case_id == case_id]

        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    async def get_timeline_summary(
        self,
        case_id: str,
    ) -> list[dict[str, Any]]:
        """Get timeline summary for a case.

        Args:
            case_id: Case identifier

        Returns:
            List of timeline events
        """
        events = await self.get_case_audit_trail(case_id)

        timeline = []
        for event in events:
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "title": event.title,
                "description": event.description,
                "actor": event.actor,
                "severity": event.severity.value,
            })

        return timeline

    async def search_events(
        self,
        query: str,
        case_id: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Search audit events.

        Args:
            query: Search query (matches title, description)
            case_id: Filter by case
            user_id: Filter by user
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results

        Returns:
            List of matching AuditEvent
        """
        events = list(self._events)

        # Apply filters
        if case_id:
            events = [e for e in events if e.case_id == case_id]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if start_date:
            events = [e for e in events if e.timestamp >= start_date]

        if end_date:
            events = [e for e in events if e.timestamp <= end_date]

        # Text search
        query_lower = query.lower()
        matching = []
        for event in events:
            if (query_lower in event.title.lower() or
                (event.description and query_lower in event.description.lower())):
                matching.append(event)

        matching.sort(key=lambda e: e.timestamp, reverse=True)

        return matching[:limit]

    async def get_statistics(self) -> dict[str, Any]:
        """Get audit trail statistics.

        Returns:
            Statistics summary
        """
        total_events = len(self._events)

        # Count by event type
        event_type_counts = {}
        for event in self._events:
            event_type_counts[event.event_type.value] = event_type_counts.get(
                event.event_type.value, 0
            ) + 1

        # Count by severity
        severity_counts = {}
        for event in self._events:
            severity_counts[event.severity.value] = severity_counts.get(
                event.severity.value, 0
            ) + 1

        # Get most recent event
        most_recent = max(self._events, key=lambda e: e.timestamp) if self._events else None

        return {
            "total_events": total_events,
            "by_type": event_type_counts,
            "by_severity": severity_counts,
            "most_recent": most_recent.timestamp.isoformat() if most_recent else None,
        }


# Singleton instance
_audit_trail: AuditTrail | None = None


def get_audit_trail() -> AuditTrail:
    """Get singleton audit trail instance."""
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail
