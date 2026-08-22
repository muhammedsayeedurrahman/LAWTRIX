"""Secure document wallet for storing and managing citizen documents.

Provides encrypted storage, access control, consent management, and audit trail.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentCategory(str, Enum):
    """Document categories for organization."""
    IDENTITY = "identity"
    ADDRESS_PROOF = "address_proof"
    INCOME_PROOF = "income_proof"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    SCHEME = "scheme"
    CASE_RELATED = "case_related"
    OTHER = "other"


class DocumentSource(str, Enum):
    """Source of document."""
    USER_UPLOAD = "user_upload"
    DIGILOCKER = "digilocker"
    GOVERNMENT_PORTAL = "government_portal"
    SYSTEM_GENERATED = "system_generated"


class AccessScope(str, Enum):
    """Access scope for documents."""
    PRIVATE = "private"  # Only user can access
    CASE_SHARED = "case_shared"  # Shared with specific case workflow
    PORTAL_SHARED = "portal_shared"  # Shared with government portal
    TEMPORARY = "temporary"  # Temporary access (expires)


class DocumentMetadata(BaseModel):
    """Document metadata."""
    model_config = ConfigDict(frozen=True)

    document_id: str = Field(..., description="Unique document identifier")
    user_id: str = Field(..., description="Document owner")

    # Document info
    file_name: str
    file_size: int
    mime_type: str
    file_hash: str = Field(..., description="SHA-256 hash for integrity")

    # Classification
    category: DocumentCategory
    document_type: str | None = Field(None, description="Specific document type (aadhaar, pan, etc.)")

    # Source tracking
    source: DocumentSource
    source_reference: str | None = Field(None, description="DigiLocker URI, upload ID, etc.")

    # Storage
    storage_path: str | None = Field(None, description="Encrypted storage path")
    encrypted: bool = Field(default=True, description="Whether file content is encrypted")

    # Access control
    access_scope: AccessScope = Field(default=AccessScope.PRIVATE)
    shared_with_cases: list[str] = Field(default_factory=list)
    shared_with_portals: list[str] = Field(default_factory=list)

    # Lifecycle
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(None, description="Document expiry (if temporary)")
    deleted_at: datetime | None = None

    # Audit
    access_count: int = Field(default=0)
    last_accessed_at: datetime | None = None


class DocumentAccessLog(BaseModel):
    """Audit log entry for document access."""
    model_config = ConfigDict(frozen=True)

    log_id: str
    document_id: str
    user_id: str
    accessed_by: str = Field(..., description="User/service accessing document")
    access_type: str = Field(..., description="view, download, share, delete")
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    access_reason: str | None = Field(None, description="Reason for access")
    case_id: str | None = Field(None, description="Case context if applicable")
    ip_address: str | None = None
    success: bool = Field(default=True)
    error_message: str | None = None


class DocumentConsent(BaseModel):
    """User consent for document sharing."""
    model_config = ConfigDict(frozen=True)

    consent_id: str
    document_id: str
    user_id: str

    # Consent details
    granted_to: str = Field(..., description="Service/portal granted access")
    purpose: str = Field(..., description="Why access is granted")
    scope: list[str] = Field(..., description="What can be done (view, download, etc.)")

    # Lifecycle
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    revoked_at: datetime | None = None

    # Context
    case_id: str | None = Field(None, description="Case for which consent was granted")

    @property
    def is_valid(self) -> bool:
        """Check if consent is still valid."""
        if self.revoked_at:
            return False
        return datetime.utcnow() < self.expires_at


class DocumentWallet:
    """Secure document wallet for managing user documents."""

    def __init__(self):
        # In production, these would use database storage and encryption service
        self._documents: dict[str, DocumentMetadata] = {}
        self._access_logs: list[DocumentAccessLog] = []
        self._consents: dict[str, DocumentConsent] = {}

    async def add_document(
        self,
        user_id: str,
        file_name: str,
        file_content: bytes,
        category: DocumentCategory,
        document_type: str | None = None,
        source: DocumentSource = DocumentSource.USER_UPLOAD,
        source_reference: str | None = None,
    ) -> DocumentMetadata:
        """Add document to wallet.

        Args:
            user_id: Document owner
            file_name: Original file name
            file_content: File content bytes
            category: Document category
            document_type: Specific document type
            source: Document source
            source_reference: Source reference (DigiLocker URI, etc.)

        Returns:
            DocumentMetadata
        """
        import hashlib
        import mimetypes
        import uuid

        # Generate document ID
        document_id = f"doc_{uuid.uuid4()}"

        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Determine MIME type
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        # In production, encrypt and store file content
        storage_path = f"/encrypted_storage/{user_id}/{document_id}"

        # Create metadata
        metadata = DocumentMetadata(
            document_id=document_id,
            user_id=user_id,
            file_name=file_name,
            file_size=len(file_content),
            mime_type=mime_type,
            file_hash=file_hash,
            category=category,
            document_type=document_type,
            source=source,
            source_reference=source_reference,
            storage_path=storage_path,
            encrypted=True,
        )

        self._documents[document_id] = metadata

        # Log upload
        await self._log_access(
            document_id=document_id,
            user_id=user_id,
            accessed_by=user_id,
            access_type="upload",
            access_reason="Document added to wallet",
        )

        return metadata

    async def get_document(
        self,
        document_id: str,
        accessed_by: str,
        access_reason: str | None = None,
        case_id: str | None = None,
    ) -> tuple[DocumentMetadata, bytes]:
        """Retrieve document from wallet.

        Args:
            document_id: Document identifier
            accessed_by: User accessing document
            access_reason: Reason for access
            case_id: Case context

        Returns:
            (DocumentMetadata, file_content)

        Raises:
            KeyError: If document not found
            PermissionError: If access denied
        """
        metadata = self._documents.get(document_id)
        if not metadata:
            raise KeyError(f"Document not found: {document_id}")

        # Check if deleted
        if metadata.deleted_at:
            raise KeyError(f"Document has been deleted: {document_id}")

        # Check if expired
        if metadata.expires_at and datetime.utcnow() > metadata.expires_at:
            raise PermissionError(f"Document has expired: {document_id}")

        # Check access permission
        if not await self._check_access_permission(metadata, accessed_by, case_id):
            raise PermissionError(f"Access denied: {document_id}")

        # In production, decrypt and retrieve from storage
        file_content = b"[Document content would be decrypted from storage]"

        # Update access metadata
        updated_metadata = metadata.model_copy(
            update={
                "access_count": metadata.access_count + 1,
                "last_accessed_at": datetime.utcnow(),
            }
        )
        self._documents[document_id] = updated_metadata

        # Log access
        await self._log_access(
            document_id=document_id,
            user_id=metadata.user_id,
            accessed_by=accessed_by,
            access_type="view",
            access_reason=access_reason,
            case_id=case_id,
        )

        return updated_metadata, file_content

    async def share_document(
        self,
        document_id: str,
        user_id: str,
        share_with: str,
        purpose: str,
        scope: list[str],
        expires_in_days: int = 30,
        case_id: str | None = None,
    ) -> DocumentConsent:
        """Share document with explicit consent.

        Args:
            document_id: Document to share
            user_id: Document owner granting consent
            share_with: Service/portal to share with
            purpose: Purpose of sharing
            scope: What can be done (view, download, etc.)
            expires_in_days: Days until consent expires
            case_id: Case context

        Returns:
            DocumentConsent

        Raises:
            KeyError: If document not found
            PermissionError: If user doesn't own document
        """
        import uuid

        metadata = self._documents.get(document_id)
        if not metadata:
            raise KeyError(f"Document not found: {document_id}")

        if metadata.user_id != user_id:
            raise PermissionError(f"User {user_id} does not own document {document_id}")

        # Create consent
        consent_id = f"consent_{uuid.uuid4()}"
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        consent = DocumentConsent(
            consent_id=consent_id,
            document_id=document_id,
            user_id=user_id,
            granted_to=share_with,
            purpose=purpose,
            scope=scope,
            expires_at=expires_at,
            case_id=case_id,
        )

        self._consents[consent_id] = consent

        # Update document access scope
        if case_id:
            shared_cases = list(metadata.shared_with_cases)
            if case_id not in shared_cases:
                shared_cases.append(case_id)

            updated_metadata = metadata.model_copy(
                update={
                    "access_scope": AccessScope.CASE_SHARED,
                    "shared_with_cases": shared_cases,
                }
            )
        else:
            shared_portals = list(metadata.shared_with_portals)
            if share_with not in shared_portals:
                shared_portals.append(share_with)

            updated_metadata = metadata.model_copy(
                update={
                    "access_scope": AccessScope.PORTAL_SHARED,
                    "shared_with_portals": shared_portals,
                }
            )

        self._documents[document_id] = updated_metadata

        # Log sharing
        await self._log_access(
            document_id=document_id,
            user_id=user_id,
            accessed_by=user_id,
            access_type="share",
            access_reason=f"Shared with {share_with}: {purpose}",
            case_id=case_id,
        )

        return consent

    async def revoke_consent(
        self,
        consent_id: str,
        user_id: str,
    ) -> DocumentConsent:
        """Revoke document sharing consent.

        Args:
            consent_id: Consent to revoke
            user_id: User revoking consent

        Returns:
            Updated DocumentConsent

        Raises:
            KeyError: If consent not found
            PermissionError: If user doesn't own consent
        """
        consent = self._consents.get(consent_id)
        if not consent:
            raise KeyError(f"Consent not found: {consent_id}")

        if consent.user_id != user_id:
            raise PermissionError(f"User {user_id} does not own consent {consent_id}")

        revoked_consent = consent.model_copy(
            update={"revoked_at": datetime.utcnow()}
        )

        self._consents[consent_id] = revoked_consent

        return revoked_consent

    async def delete_document(
        self,
        document_id: str,
        user_id: str,
    ) -> DocumentMetadata:
        """Soft-delete document.

        Args:
            document_id: Document to delete
            user_id: User deleting document

        Returns:
            Updated DocumentMetadata

        Raises:
            KeyError: If document not found
            PermissionError: If user doesn't own document
        """
        metadata = self._documents.get(document_id)
        if not metadata:
            raise KeyError(f"Document not found: {document_id}")

        if metadata.user_id != user_id:
            raise PermissionError(f"User {user_id} does not own document {document_id}")

        deleted_metadata = metadata.model_copy(
            update={"deleted_at": datetime.utcnow()}
        )

        self._documents[document_id] = deleted_metadata

        # Log deletion
        await self._log_access(
            document_id=document_id,
            user_id=user_id,
            accessed_by=user_id,
            access_type="delete",
            access_reason="Document deleted by owner",
        )

        return deleted_metadata

    async def list_user_documents(
        self,
        user_id: str,
        category: DocumentCategory | None = None,
        include_deleted: bool = False,
    ) -> list[DocumentMetadata]:
        """List documents owned by user.

        Args:
            user_id: Document owner
            category: Filter by category
            include_deleted: Include deleted documents

        Returns:
            List of DocumentMetadata
        """
        documents = [
            doc for doc in self._documents.values()
            if doc.user_id == user_id
        ]

        if not include_deleted:
            documents = [doc for doc in documents if not doc.deleted_at]

        if category:
            documents = [doc for doc in documents if doc.category == category]

        # Sort by upload date (newest first)
        documents.sort(key=lambda d: d.uploaded_at, reverse=True)

        return documents

    async def get_document_access_logs(
        self,
        document_id: str,
        user_id: str,
    ) -> list[DocumentAccessLog]:
        """Get access logs for a document.

        Args:
            document_id: Document identifier
            user_id: Document owner

        Returns:
            List of DocumentAccessLog

        Raises:
            PermissionError: If user doesn't own document
        """
        metadata = self._documents.get(document_id)
        if not metadata:
            raise KeyError(f"Document not found: {document_id}")

        if metadata.user_id != user_id:
            raise PermissionError(f"User {user_id} does not own document {document_id}")

        logs = [
            log for log in self._access_logs
            if log.document_id == document_id
        ]

        # Sort by access time (newest first)
        logs.sort(key=lambda l: l.accessed_at, reverse=True)

        return logs

    async def _check_access_permission(
        self,
        metadata: DocumentMetadata,
        accessed_by: str,
        case_id: str | None = None,
    ) -> bool:
        """Check if user/service has permission to access document.

        Args:
            metadata: Document metadata
            accessed_by: User/service accessing
            case_id: Case context

        Returns:
            True if access allowed
        """
        # Owner always has access
        if accessed_by == metadata.user_id:
            return True

        # Check access scope
        if metadata.access_scope == AccessScope.PRIVATE:
            return False

        if metadata.access_scope == AccessScope.CASE_SHARED:
            return case_id in metadata.shared_with_cases if case_id else False

        if metadata.access_scope == AccessScope.PORTAL_SHARED:
            return accessed_by in metadata.shared_with_portals

        # Check if there's valid consent
        for consent in self._consents.values():
            if (consent.document_id == metadata.document_id and
                consent.granted_to == accessed_by and
                consent.is_valid):
                return True

        return False

    async def _log_access(
        self,
        document_id: str,
        user_id: str,
        accessed_by: str,
        access_type: str,
        access_reason: str | None = None,
        case_id: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """Log document access.

        Args:
            document_id: Document accessed
            user_id: Document owner
            accessed_by: User/service accessing
            access_type: Type of access (view, download, share, delete)
            access_reason: Reason for access
            case_id: Case context
            success: Whether access succeeded
            error_message: Error message if failed
        """
        import uuid

        log = DocumentAccessLog(
            log_id=f"log_{uuid.uuid4()}",
            document_id=document_id,
            user_id=user_id,
            accessed_by=accessed_by,
            access_type=access_type,
            access_reason=access_reason,
            case_id=case_id,
            success=success,
            error_message=error_message,
        )

        self._access_logs.append(log)
