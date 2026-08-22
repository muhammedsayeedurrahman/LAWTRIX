"""SQLAlchemy ORM models for PostgreSQL database.

These models define the database schema for persisting citizen cases,
documents, consents, and automation sessions.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Citizen(Base):
    """Citizen/user table."""
    __tablename__ = "citizens"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cases: Mapped[list["Case"]] = relationship("Case", back_populates="citizen")
    documents: Mapped[list["DocumentRecord"]] = relationship("DocumentRecord", back_populates="citizen")


class Case(Base):
    """Case table - stores full CitizenCase as JSONB."""
    __tablename__ = "cases"

    case_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    citizen_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), index=True)

    # Denormalized fields for fast querying
    workflow: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    intent_category: Mapped[str | None] = mapped_column(String(100), index=True)

    # Full case data as JSONB
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    citizen: Mapped[Citizen | None] = relationship("Citizen", back_populates="cases")
    timeline: Mapped[list["CaseTimeline"]] = relationship("CaseTimeline", back_populates="case", cascade="all, delete-orphan")
    automation_sessions: Mapped[list["AutomationSession"]] = relationship("AutomationSession", back_populates="case")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_case_workflow_status", "workflow", "status"),
        Index("idx_case_citizen_created", "citizen_id", "created_at"),
    )


class CaseTimeline(Base):
    """Case timeline events."""
    __tablename__ = "case_timeline"

    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.case_id"), nullable=False, index=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(50), nullable=False)  # system|user|authority
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON)

    # Relationship
    case: Mapped[Case] = relationship("Case", back_populates="timeline")

    __table_args__ = (
        Index("idx_timeline_case_timestamp", "case_id", "timestamp"),
    )


class DocumentRecord(Base):
    """Document storage metadata."""
    __tablename__ = "documents"

    doc_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    citizen_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=False, index=True)

    doc_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)  # S3 key or file path
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column()

    encrypted: Mapped[bool] = mapped_column(Boolean, default=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(50), default="user")  # user|system|digilocker

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationship
    citizen: Mapped[Citizen] = relationship("Citizen", back_populates="documents")
    consents: Mapped[list["Consent"]] = relationship("Consent", back_populates="document")


class Consent(Base):
    """User consent records."""
    __tablename__ = "consents"

    consent_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    doc_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.doc_id"), index=True)
    citizen_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=False, index=True)

    # Consent types
    storage_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    sharing_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    automation_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    digilocker_access: Mapped[bool] = mapped_column(Boolean, default=False)

    purpose: Mapped[str | None] = mapped_column(Text)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationship
    document: Mapped[DocumentRecord | None] = relationship("DocumentRecord", back_populates="consents")


class AutomationSession(Base):
    """Browser automation session state (OpenClaw)."""
    __tablename__ = "automation_sessions"

    session_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.case_id"), nullable=False, index=True)

    portal_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    # Full session state as JSONB (OpenClaw SessionState)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationship
    case: Mapped[Case] = relationship("Case", back_populates="automation_sessions")

    __table_args__ = (
        Index("idx_automation_case_status", "case_id", "status"),
    )
