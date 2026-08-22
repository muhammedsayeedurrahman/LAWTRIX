"""Case tracking and reminder system.

Provides comprehensive case tracking, status monitoring, and automated reminders.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CaseStatus(str, Enum):
    """Overall case status."""
    DRAFT = "draft"  # Case being prepared
    READY = "ready"  # Ready for action
    IN_PROGRESS = "in_progress"  # Action in progress
    SUBMITTED = "submitted"  # Submitted to authority
    UNDER_REVIEW = "under_review"  # Authority reviewing
    PENDING_USER_ACTION = "pending_user_action"  # User action needed
    PENDING_RESPONSE = "pending_response"  # Waiting for authority response
    RESOLVED = "resolved"  # Case resolved
    CLOSED = "closed"  # Case closed
    APPEALED = "appealed"  # Under appeal


class ReminderType(str, Enum):
    """Types of reminders."""
    STATUS_CHECK = "status_check"  # Check case status
    DEADLINE_APPROACHING = "deadline_approaching"  # Deadline coming up
    RESPONSE_OVERDUE = "response_overdue"  # Expected response overdue
    ACTION_REQUIRED = "action_required"  # User action needed
    FOLLOW_UP = "follow_up"  # Follow up required
    APPEAL_WINDOW = "appeal_window"  # Appeal deadline approaching


class TimelineEvent(BaseModel):
    """Single event in case timeline."""
    model_config = ConfigDict(frozen=True)

    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(..., description="Type of event (created, updated, submitted, etc.)")
    title: str = Field(..., description="Short event description")
    description: str | None = Field(None, description="Detailed description")
    actor: str | None = Field(None, description="Who performed this action")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional event data")


class CaseTimeline(BaseModel):
    """Complete timeline of case events."""
    model_config = ConfigDict(frozen=True)

    case_id: str
    events: list[TimelineEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_latest_event(self) -> TimelineEvent | None:
        """Get most recent event."""
        if not self.events:
            return None
        return max(self.events, key=lambda e: e.timestamp)


class CaseReminder(BaseModel):
    """Reminder for case follow-up."""
    model_config = ConfigDict(frozen=True)

    reminder_id: str
    case_id: str
    reminder_type: ReminderType

    # Scheduling
    scheduled_at: datetime
    sent_at: datetime | None = None
    dismissed_at: datetime | None = None

    # Content
    title: str
    message: str
    action_required: str | None = None

    # Context
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_due(self) -> bool:
        """Check if reminder is due."""
        return datetime.utcnow() >= self.scheduled_at and not self.sent_at and not self.dismissed_at

    @property
    def is_active(self) -> bool:
        """Check if reminder is still active."""
        return not self.sent_at and not self.dismissed_at


class CaseTrackingInfo(BaseModel):
    """Comprehensive case tracking information."""
    model_config = ConfigDict(frozen=True)

    case_id: str
    workflow_name: str
    current_status: CaseStatus

    # Submission info
    reference_id: str | None = None
    submitted_at: datetime | None = None
    authority: str | None = None
    portal: str | None = None

    # Status tracking
    last_status_check: datetime | None = None
    next_status_check: datetime | None = None
    status_source: str | None = Field(None, description="Where status comes from")

    # Deadlines
    expected_response_by: datetime | None = None
    appeal_deadline: datetime | None = None

    # Next actions
    next_action: str | None = None
    next_action_by: datetime | None = None

    # Progress
    timeline: list[TimelineEvent] = Field(default_factory=list)
    reminders: list[CaseReminder] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)


class CaseTracker:
    """Case tracking and reminder manager."""

    def __init__(self):
        # In production, use database storage
        self._tracking_info: dict[str, CaseTrackingInfo] = {}
        self._timelines: dict[str, CaseTimeline] = {}

    async def create_tracking(
        self,
        case_id: str,
        workflow_name: str,
        initial_status: CaseStatus = CaseStatus.DRAFT,
    ) -> CaseTrackingInfo:
        """Create tracking for a new case.

        Args:
            case_id: Case identifier
            workflow_name: Workflow type
            initial_status: Initial case status

        Returns:
            CaseTrackingInfo
        """
        tracking = CaseTrackingInfo(
            case_id=case_id,
            workflow_name=workflow_name,
            current_status=initial_status,
        )

        self._tracking_info[case_id] = tracking

        # Create timeline
        timeline = CaseTimeline(case_id=case_id)
        self._timelines[case_id] = timeline

        # Add creation event
        await self.add_timeline_event(
            case_id=case_id,
            event_type="created",
            title="Case Created",
            description=f"Case created for {workflow_name} workflow",
        )

        return tracking

    async def update_status(
        self,
        case_id: str,
        new_status: CaseStatus,
        status_source: str | None = None,
        actor: str | None = None,
    ) -> CaseTrackingInfo:
        """Update case status.

        Args:
            case_id: Case identifier
            new_status: New status
            status_source: Where status update came from
            actor: Who updated the status

        Returns:
            Updated CaseTrackingInfo
        """
        tracking = self._tracking_info.get(case_id)
        if not tracking:
            raise KeyError(f"Tracking not found for case: {case_id}")

        old_status = tracking.current_status

        # Update tracking
        updated_tracking = tracking.model_copy(
            update={
                "current_status": new_status,
                "status_source": status_source,
                "last_updated_at": datetime.utcnow(),
                "last_status_check": datetime.utcnow(),
            }
        )

        self._tracking_info[case_id] = updated_tracking

        # Add timeline event
        await self.add_timeline_event(
            case_id=case_id,
            event_type="status_changed",
            title=f"Status: {old_status.value} → {new_status.value}",
            description=f"Case status changed from {old_status.value} to {new_status.value}",
            actor=actor,
            metadata={"old_status": old_status.value, "new_status": new_status.value},
        )

        # Schedule automatic reminders based on new status
        await self._schedule_automatic_reminders(case_id, new_status)

        return updated_tracking

    async def record_submission(
        self,
        case_id: str,
        reference_id: str,
        authority: str,
        portal: str | None = None,
        expected_response_days: int = 30,
    ) -> CaseTrackingInfo:
        """Record case submission.

        Args:
            case_id: Case identifier
            reference_id: Submission reference ID
            authority: Authority submitted to
            portal: Portal used for submission
            expected_response_days: Expected response time in days

        Returns:
            Updated CaseTrackingInfo
        """
        tracking = self._tracking_info.get(case_id)
        if not tracking:
            raise KeyError(f"Tracking not found for case: {case_id}")

        submitted_at = datetime.utcnow()
        expected_response_by = submitted_at + timedelta(days=expected_response_days)

        updated_tracking = tracking.model_copy(
            update={
                "current_status": CaseStatus.SUBMITTED,
                "reference_id": reference_id,
                "submitted_at": submitted_at,
                "authority": authority,
                "portal": portal,
                "expected_response_by": expected_response_by,
                "last_updated_at": submitted_at,
            }
        )

        self._tracking_info[case_id] = updated_tracking

        # Add timeline event
        await self.add_timeline_event(
            case_id=case_id,
            event_type="submitted",
            title="Submitted to Authority",
            description=f"Submitted to {authority} with reference ID: {reference_id}",
            metadata={
                "reference_id": reference_id,
                "authority": authority,
                "expected_response_by": expected_response_by.isoformat(),
            },
        )

        # Schedule status check reminders
        await self._schedule_submission_reminders(case_id, expected_response_days)

        return updated_tracking

    async def add_timeline_event(
        self,
        case_id: str,
        event_type: str,
        title: str,
        description: str | None = None,
        actor: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        """Add event to case timeline.

        Args:
            case_id: Case identifier
            event_type: Event type
            title: Short title
            description: Detailed description
            actor: Who performed action
            metadata: Additional data

        Returns:
            Created TimelineEvent
        """
        import uuid

        timeline = self._timelines.get(case_id)
        if not timeline:
            timeline = CaseTimeline(case_id=case_id)
            self._timelines[case_id] = timeline

        event = TimelineEvent(
            event_id=f"evt_{uuid.uuid4()}",
            event_type=event_type,
            title=title,
            description=description,
            actor=actor,
            metadata=metadata or {},
        )

        # Add event to timeline
        new_events = list(timeline.events) + [event]
        updated_timeline = timeline.model_copy(
            update={
                "events": new_events,
                "last_updated_at": datetime.utcnow(),
            }
        )

        self._timelines[case_id] = updated_timeline

        return event

    async def schedule_reminder(
        self,
        case_id: str,
        reminder_type: ReminderType,
        scheduled_at: datetime,
        title: str,
        message: str,
        action_required: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CaseReminder:
        """Schedule a reminder for case.

        Args:
            case_id: Case identifier
            reminder_type: Type of reminder
            scheduled_at: When to send reminder
            title: Reminder title
            message: Reminder message
            action_required: Action user should take
            metadata: Additional data

        Returns:
            Created CaseReminder
        """
        import uuid

        tracking = self._tracking_info.get(case_id)
        if not tracking:
            raise KeyError(f"Tracking not found for case: {case_id}")

        reminder = CaseReminder(
            reminder_id=f"rem_{uuid.uuid4()}",
            case_id=case_id,
            reminder_type=reminder_type,
            scheduled_at=scheduled_at,
            title=title,
            message=message,
            action_required=action_required,
            metadata=metadata or {},
        )

        # Add reminder to tracking
        new_reminders = list(tracking.reminders) + [reminder]
        updated_tracking = tracking.model_copy(
            update={
                "reminders": new_reminders,
                "last_updated_at": datetime.utcnow(),
            }
        )

        self._tracking_info[case_id] = updated_tracking

        return reminder

    async def get_due_reminders(self, case_id: str | None = None) -> list[CaseReminder]:
        """Get all due reminders.

        Args:
            case_id: Optional case to filter by

        Returns:
            List of due reminders
        """
        due_reminders = []

        tracking_items = [self._tracking_info.get(case_id)] if case_id else self._tracking_info.values()

        for tracking in tracking_items:
            if tracking:
                due_reminders.extend([r for r in tracking.reminders if r.is_due])

        return due_reminders

    async def mark_reminder_sent(self, reminder_id: str, case_id: str) -> CaseReminder:
        """Mark reminder as sent.

        Args:
            reminder_id: Reminder identifier
            case_id: Case identifier

        Returns:
            Updated CaseReminder
        """
        tracking = self._tracking_info.get(case_id)
        if not tracking:
            raise KeyError(f"Tracking not found for case: {case_id}")

        # Find and update reminder
        updated_reminders = []
        updated_reminder = None

        for reminder in tracking.reminders:
            if reminder.reminder_id == reminder_id:
                updated_reminder = reminder.model_copy(
                    update={"sent_at": datetime.utcnow()}
                )
                updated_reminders.append(updated_reminder)
            else:
                updated_reminders.append(reminder)

        if not updated_reminder:
            raise KeyError(f"Reminder not found: {reminder_id}")

        # Update tracking
        updated_tracking = tracking.model_copy(
            update={"reminders": updated_reminders}
        )
        self._tracking_info[case_id] = updated_tracking

        return updated_reminder

    async def get_case_summary(self, case_id: str) -> dict[str, Any]:
        """Get comprehensive case summary.

        Args:
            case_id: Case identifier

        Returns:
            Case summary dict
        """
        tracking = self._tracking_info.get(case_id)
        timeline = self._timelines.get(case_id)

        if not tracking:
            raise KeyError(f"Tracking not found for case: {case_id}")

        # Get active reminders
        active_reminders = [r for r in tracking.reminders if r.is_active]

        # Get recent events (last 10)
        recent_events = []
        if timeline:
            sorted_events = sorted(timeline.events, key=lambda e: e.timestamp, reverse=True)
            recent_events = sorted_events[:10]

        return {
            "case_id": case_id,
            "workflow": tracking.workflow_name,
            "status": tracking.current_status.value,
            "reference_id": tracking.reference_id,
            "submitted_at": tracking.submitted_at.isoformat() if tracking.submitted_at else None,
            "authority": tracking.authority,
            "next_action": tracking.next_action,
            "next_action_by": tracking.next_action_by.isoformat() if tracking.next_action_by else None,
            "expected_response_by": tracking.expected_response_by.isoformat() if tracking.expected_response_by else None,
            "active_reminders_count": len(active_reminders),
            "recent_events": [
                {
                    "type": e.event_type,
                    "title": e.title,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in recent_events
            ],
        }

    async def get_my_cases(
        self,
        user_id: str,
        status_filter: CaseStatus | None = None,
    ) -> list[dict[str, Any]]:
        """Get all cases for a user.

        Args:
            user_id: User identifier
            status_filter: Optional status filter

        Returns:
            List of case summaries
        """
        # In production, filter by user_id from database
        # For now, return all cases (would be filtered by user_id)

        cases = []
        for case_id, tracking in self._tracking_info.items():
            if status_filter and tracking.current_status != status_filter:
                continue

            cases.append(await self.get_case_summary(case_id))

        # Sort by last updated (newest first)
        cases.sort(key=lambda c: c.get("submitted_at") or c.get("case_id"), reverse=True)

        return cases

    async def _schedule_automatic_reminders(
        self,
        case_id: str,
        status: CaseStatus,
    ) -> None:
        """Schedule automatic reminders based on status.

        Args:
            case_id: Case identifier
            status: New case status
        """
        if status == CaseStatus.SUBMITTED:
            # Schedule status check reminder in 15 days
            await self.schedule_reminder(
                case_id=case_id,
                reminder_type=ReminderType.STATUS_CHECK,
                scheduled_at=datetime.utcnow() + timedelta(days=15),
                title="Check Case Status",
                message="It's been 15 days since submission. Check the status of your case.",
                action_required="Visit the tracking portal or contact the authority",
            )

        elif status == CaseStatus.PENDING_USER_ACTION:
            # Schedule immediate action reminder
            await self.schedule_reminder(
                case_id=case_id,
                reminder_type=ReminderType.ACTION_REQUIRED,
                scheduled_at=datetime.utcnow() + timedelta(hours=24),
                title="Action Required",
                message="Your case requires action from you.",
                action_required="Review the case and take required action",
            )

    async def _schedule_submission_reminders(
        self,
        case_id: str,
        expected_response_days: int,
    ) -> None:
        """Schedule reminders after submission.

        Args:
            case_id: Case identifier
            expected_response_days: Expected response time
        """
        # Check status 3 days before expected response
        check_date = datetime.utcnow() + timedelta(days=expected_response_days - 3)
        await self.schedule_reminder(
            case_id=case_id,
            reminder_type=ReminderType.STATUS_CHECK,
            scheduled_at=check_date,
            title="Response Due Soon",
            message=f"Response expected in 3 days. Check status to see if any updates.",
            action_required="Check case status on portal",
        )

        # Overdue reminder if no response
        overdue_date = datetime.utcnow() + timedelta(days=expected_response_days + 2)
        await self.schedule_reminder(
            case_id=case_id,
            reminder_type=ReminderType.RESPONSE_OVERDUE,
            scheduled_at=overdue_date,
            title="Response Overdue",
            message=f"Expected response by {expected_response_days} days has not been received.",
            action_required="Follow up with authority or file first appeal if applicable",
        )
