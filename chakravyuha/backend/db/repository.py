"""Repository pattern for database operations on CitizenCase.

Provides CRUD operations and common queries for cases.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import Case, CaseTimeline, Citizen
from backend.models.citizen_case import CitizenCase, EventType, TimelineEvent


class CaseRepository:
    """Repository for CitizenCase database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, case: CitizenCase, citizen_id: UUID | None = None) -> Case:
        """Create a new case in the database."""
        db_case = Case(
            case_id=UUID(case.case_id) if isinstance(case.case_id, str) else case.case_id,
            citizen_id=citizen_id,
            workflow=case.workflow.name,
            status=case.workflow.status.value,
            intent_category=case.intent.category.value,
            data=case.model_dump(mode="json"),
            created_at=case.created_at,
            updated_at=case.updated_at,
        )
        self.db.add(db_case)
        await self.db.flush()
        return db_case

    async def get(self, case_id: UUID | str) -> CitizenCase | None:
        """Get a case by ID."""
        if isinstance(case_id, str):
            case_id = UUID(case_id)

        result = await self.db.execute(
            select(Case).where(Case.case_id == case_id)
        )
        db_case = result.scalar_one_or_none()

        if db_case:
            return CitizenCase.model_validate(db_case.data)
        return None

    async def update(self, case: CitizenCase) -> Case:
        """Update an existing case."""
        case_id = UUID(case.case_id) if isinstance(case.case_id, str) else case.case_id

        result = await self.db.execute(
            select(Case).where(Case.case_id == case_id)
        )
        db_case = result.scalar_one_or_none()

        if not db_case:
            raise ValueError(f"Case {case_id} not found")

        db_case.workflow = case.workflow.name
        db_case.status = case.workflow.status.value
        db_case.intent_category = case.intent.category.value
        db_case.data = case.model_dump(mode="json")
        db_case.updated_at = datetime.utcnow()

        await self.db.flush()
        return db_case

    async def delete(self, case_id: UUID | str) -> bool:
        """Delete a case."""
        if isinstance(case_id, str):
            case_id = UUID(case_id)

        result = await self.db.execute(
            select(Case).where(Case.case_id == case_id)
        )
        db_case = result.scalar_one_or_none()

        if db_case:
            await self.db.delete(db_case)
            await self.db.flush()
            return True
        return False

    async def list_by_citizen(
        self,
        citizen_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[CitizenCase]:
        """List all cases for a citizen."""
        result = await self.db.execute(
            select(Case)
            .where(Case.citizen_id == citizen_id)
            .order_by(Case.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        db_cases = result.scalars().all()
        return [CitizenCase.model_validate(c.data) for c in db_cases]

    async def list_by_workflow(
        self,
        workflow: str,
        status: str | None = None,
        limit: int = 50
    ) -> Sequence[CitizenCase]:
        """List cases by workflow and optionally status."""
        query = select(Case).where(Case.workflow == workflow)

        if status:
            query = query.where(Case.status == status)

        query = query.order_by(Case.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        db_cases = result.scalars().all()
        return [CitizenCase.model_validate(c.data) for c in db_cases]

    async def add_timeline_event(
        self,
        case_id: UUID | str,
        event: TimelineEvent
    ) -> CaseTimeline:
        """Add a timeline event to a case."""
        if isinstance(case_id, str):
            case_id = UUID(case_id)

        db_event = CaseTimeline(
            case_id=case_id,
            timestamp=event.timestamp,
            event_type=event.event_type.value,
            actor=event.actor,
            description=event.description,
            details=event.details,
        )
        self.db.add(db_event)
        await self.db.flush()
        return db_event

    async def get_timeline(self, case_id: UUID | str) -> Sequence[TimelineEvent]:
        """Get all timeline events for a case."""
        if isinstance(case_id, str):
            case_id = UUID(case_id)

        result = await self.db.execute(
            select(CaseTimeline)
            .where(CaseTimeline.case_id == case_id)
            .order_by(CaseTimeline.timestamp)
        )
        db_events = result.scalars().all()

        return [
            TimelineEvent(
                event_id=str(e.event_id),
                timestamp=e.timestamp,
                event_type=EventType(e.event_type),
                actor=e.actor,
                description=e.description,
                details=e.details or {},
            )
            for e in db_events
        ]


class CitizenRepository:
    """Repository for Citizen database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, phone: str, name: str | None = None) -> Citizen:
        """Create a new citizen."""
        citizen = Citizen(phone=phone, name=name)
        self.db.add(citizen)
        await self.db.flush()
        return citizen

    async def get_by_phone(self, phone: str) -> Citizen | None:
        """Get citizen by phone number."""
        result = await self.db.execute(
            select(Citizen).where(Citizen.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, citizen_id: UUID) -> Citizen | None:
        """Get citizen by ID."""
        result = await self.db.execute(
            select(Citizen).where(Citizen.id == citizen_id)
        )
        return result.scalar_one_or_none()

    async def update(self, citizen_id: UUID, **kwargs) -> Citizen:
        """Update citizen details."""
        result = await self.db.execute(
            select(Citizen).where(Citizen.id == citizen_id)
        )
        citizen = result.scalar_one_or_none()

        if not citizen:
            raise ValueError(f"Citizen {citizen_id} not found")

        for key, value in kwargs.items():
            if hasattr(citizen, key):
                setattr(citizen, key, value)

        citizen.updated_at = datetime.utcnow()
        await self.db.flush()
        return citizen
