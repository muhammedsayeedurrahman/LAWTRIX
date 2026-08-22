"""Document intelligence pipeline for extraction and classification.

Handles document upload → classification → OCR → fact extraction → workflow routing.
"""

from __future__ import annotations

import hashlib
import mimetypes
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Types of documents that can be processed."""
    # Identity documents
    AADHAAR = "aadhaar"
    PAN_CARD = "pan_card"
    VOTER_ID = "voter_id"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"

    # Address proof
    ELECTRICITY_BILL = "electricity_bill"
    WATER_BILL = "water_bill"
    RENT_AGREEMENT = "rent_agreement"
    PROPERTY_TAX = "property_tax"

    # Income proof
    SALARY_SLIP = "salary_slip"
    BANK_STATEMENT = "bank_statement"
    ITR = "itr"
    FORM_16 = "form_16"

    # Employment documents
    APPOINTMENT_LETTER = "appointment_letter"
    EXPERIENCE_LETTER = "experience_letter"
    TERMINATION_LETTER = "termination_letter"

    # Consumer documents
    INVOICE = "invoice"
    RECEIPT = "receipt"
    WARRANTY_CARD = "warranty_card"

    # Government documents
    GOVERNMENT_NOTICE = "government_notice"
    RTI_REPLY = "rti_reply"
    COURT_ORDER = "court_order"
    SCHEME_CERTIFICATE = "scheme_certificate"

    # Other
    PHOTO = "photo"
    UNKNOWN = "unknown"


class DocumentClassification(BaseModel):
    """Result of document classification."""
    model_config = ConfigDict(frozen=True)

    document_type: DocumentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    alternative_types: list[tuple[DocumentType, float]] = Field(default_factory=list)


class ExtractedFact(BaseModel):
    """A single extracted fact from document."""
    model_config = ConfigDict(frozen=True)

    field_name: str = Field(..., description="Name of the field")
    value: Any = Field(..., description="Extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in extraction")
    source_location: str | None = Field(None, description="Where in document this was found")
    requires_verification: bool = Field(default=True, description="Whether user should verify")


class DocumentExtractionResult(BaseModel):
    """Result of document processing."""
    model_config = ConfigDict(frozen=True)

    document_id: str
    document_type: DocumentType
    classification_confidence: float

    # Extracted content
    raw_text: str | None = Field(None, description="Full OCR text")
    extracted_facts: list[ExtractedFact] = Field(default_factory=list)

    # Metadata
    file_name: str
    file_size: int
    mime_type: str
    file_hash: str = Field(..., description="SHA-256 hash of file")

    # Processing metadata
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    ocr_engine: str | None = None
    extraction_method: str = "rule_based"

    # Workflow routing
    suggested_workflow: str | None = Field(None, description="Suggested workflow based on document")
    routing_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DocumentIntelligence:
    """Document intelligence pipeline."""

    # Document type patterns (keywords that suggest document type)
    CLASSIFICATION_PATTERNS = {
        DocumentType.AADHAAR: [
            "aadhaar",
            "आधार",
            "unique identification",
            "uidai",
        ],
        DocumentType.PAN_CARD: [
            "permanent account number",
            "income tax department",
            "pan card",
        ],
        DocumentType.SALARY_SLIP: [
            "salary slip",
            "pay slip",
            "payslip",
            "gross salary",
            "net salary",
            "deductions",
            "basic pay",
        ],
        DocumentType.RENT_AGREEMENT: [
            "rent agreement",
            "rental agreement",
            "tenancy agreement",
            "lease deed",
            "landlord",
            "tenant",
            "monthly rent",
        ],
        DocumentType.INVOICE: [
            "invoice",
            "bill",
            "receipt",
            "gst",
            "total amount",
            "item description",
        ],
        DocumentType.TERMINATION_LETTER: [
            "termination",
            "terminated",
            "notice period",
            "last working day",
            "employment terminated",
        ],
        DocumentType.RTI_REPLY: [
            "right to information",
            "rti act",
            "public information officer",
            "pio",
            "application number",
        ],
        DocumentType.GOVERNMENT_NOTICE: [
            "government of",
            "ministry of",
            "department of",
            "notification",
            "circular",
        ],
    }

    def __init__(self):
        pass

    async def process_document(
        self,
        file_path: str | Path,
        file_content: bytes | None = None,
    ) -> DocumentExtractionResult:
        """Process a document: classify, extract text, extract facts.

        Args:
            file_path: Path to document file
            file_content: File content bytes (optional, will read from path if not provided)

        Returns:
            DocumentExtractionResult with classification and extracted data
        """
        file_path = Path(file_path)

        # Read file if content not provided
        if file_content is None:
            with open(file_path, "rb") as f:
                file_content = f.read()

        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Get file metadata
        file_size = len(file_content)
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

        # Generate document ID
        document_id = f"doc_{file_hash[:16]}_{datetime.utcnow().timestamp()}"

        # Step 1: Extract text (OCR or direct text extraction)
        raw_text = await self._extract_text(file_content, mime_type)

        # Step 2: Classify document
        classification = await self._classify_document(raw_text, file_path.name)

        # Step 3: Extract facts based on document type
        extracted_facts = await self._extract_facts(
            raw_text,
            classification.document_type,
        )

        # Step 4: Suggest workflow
        suggested_workflow, routing_confidence = self._suggest_workflow(
            classification.document_type,
            extracted_facts,
        )

        return DocumentExtractionResult(
            document_id=document_id,
            document_type=classification.document_type,
            classification_confidence=classification.confidence,
            raw_text=raw_text,
            extracted_facts=extracted_facts,
            file_name=file_path.name,
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            ocr_engine="placeholder_ocr",  # Would use actual OCR engine
            extraction_method="rule_based",
            suggested_workflow=suggested_workflow,
            routing_confidence=routing_confidence,
        )

    async def _extract_text(self, file_content: bytes, mime_type: str) -> str:
        """Extract text from document.

        For production, this would use:
        - Tesseract OCR for images
        - pdfplumber/PyPDF2 for PDFs
        - python-docx for Word documents

        Args:
            file_content: File content bytes
            mime_type: MIME type of file

        Returns:
            Extracted text
        """
        # Placeholder implementation
        # In production, integrate with actual OCR/extraction libraries

        if mime_type.startswith("image/"):
            # Would use Tesseract OCR here
            return "[OCR text would be extracted here]"
        elif mime_type == "application/pdf":
            # Would use pdfplumber here
            return "[PDF text would be extracted here]"
        elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            # Would use python-docx here
            return "[Word document text would be extracted here]"
        else:
            try:
                return file_content.decode("utf-8")
            except UnicodeDecodeError:
                return "[Binary file - no text extraction available]"

    async def _classify_document(
        self,
        text: str,
        filename: str,
    ) -> DocumentClassification:
        """Classify document based on content and filename.

        Args:
            text: Extracted text
            filename: Original filename

        Returns:
            DocumentClassification with type and confidence
        """
        text_lower = text.lower()
        filename_lower = filename.lower()

        # Score each document type
        scores: dict[DocumentType, float] = {}

        for doc_type, patterns in self.CLASSIFICATION_PATTERNS.items():
            score = 0.0
            matched_patterns = []

            for pattern in patterns:
                # Check in text
                if pattern.lower() in text_lower:
                    score += 1.0
                    matched_patterns.append(pattern)

                # Check in filename (weighted higher)
                if pattern.lower() in filename_lower:
                    score += 2.0
                    matched_patterns.append(f"{pattern} (filename)")

            if score > 0:
                # Normalize score
                scores[doc_type] = min(score / (len(patterns) + 2), 1.0)

        if not scores:
            return DocumentClassification(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                reasoning="No matching patterns found",
            )

        # Get top classification
        top_type = max(scores, key=scores.get)
        top_confidence = scores[top_type]

        # Get alternatives
        alternatives = [
            (doc_type, score)
            for doc_type, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
            if doc_type != top_type
        ][:3]

        return DocumentClassification(
            document_type=top_type,
            confidence=top_confidence,
            reasoning=f"Matched patterns for {top_type.value}",
            alternative_types=alternatives,
        )

    async def _extract_facts(
        self,
        text: str,
        document_type: DocumentType,
    ) -> list[ExtractedFact]:
        """Extract structured facts from document based on type.

        Args:
            text: Extracted text
            document_type: Classified document type

        Returns:
            List of extracted facts
        """
        import re

        facts = []
        text_lower = text.lower()

        # Common extractors

        # Extract amounts (currency)
        amount_patterns = [
            r"(?:rs\.?|inr|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)",
            r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rs\.?|rupees?)",
        ]
        for pattern in amount_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                amount_str = match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                    facts.append(ExtractedFact(
                        field_name="amount",
                        value=amount,
                        confidence=0.8,
                        source_location=f"Position {match.start()}-{match.end()}",
                    ))
                    break  # Only take first match
                except ValueError:
                    pass

        # Extract dates
        date_patterns = [
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        ]
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                facts.append(ExtractedFact(
                    field_name="date",
                    value=match.group(1),
                    confidence=0.7,
                    source_location=f"Position {match.start()}-{match.end()}",
                ))
                break  # Only take first match

        # Document-specific extractors

        if document_type == DocumentType.SALARY_SLIP:
            # Extract employee name
            name_patterns = [
                r"employee\s+name\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"name\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ]
            for pattern in name_patterns:
                match = re.search(pattern, text)
                if match:
                    facts.append(ExtractedFact(
                        field_name="employee_name",
                        value=match.group(1),
                        confidence=0.9,
                    ))
                    break

            # Extract salary components
            if "gross salary" in text_lower:
                facts.append(ExtractedFact(
                    field_name="document_contains",
                    value="salary_details",
                    confidence=1.0,
                ))

        elif document_type == DocumentType.RENT_AGREEMENT:
            # Extract landlord/tenant
            landlord_pattern = r"landlord\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            tenant_pattern = r"tenant\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"

            landlord_match = re.search(landlord_pattern, text)
            if landlord_match:
                facts.append(ExtractedFact(
                    field_name="landlord_name",
                    value=landlord_match.group(1),
                    confidence=0.8,
                ))

            tenant_match = re.search(tenant_pattern, text)
            if tenant_match:
                facts.append(ExtractedFact(
                    field_name="tenant_name",
                    value=tenant_match.group(1),
                    confidence=0.8,
                ))

            # Extract rent amount
            rent_pattern = r"(?:monthly\s+)?rent\s*:?\s*(?:rs\.?|₹)?\s*(\d+(?:,\d+)*)"
            rent_match = re.search(rent_pattern, text_lower)
            if rent_match:
                rent_str = rent_match.group(1).replace(",", "")
                facts.append(ExtractedFact(
                    field_name="monthly_rent",
                    value=float(rent_str),
                    confidence=0.9,
                ))

        elif document_type == DocumentType.INVOICE:
            # Extract seller
            seller_pattern = r"(?:seller|from)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            seller_match = re.search(seller_pattern, text)
            if seller_match:
                facts.append(ExtractedFact(
                    field_name="seller_name",
                    value=seller_match.group(1),
                    confidence=0.7,
                ))

            # Invoice number
            invoice_pattern = r"invoice\s+(?:no\.?|number)\s*:?\s*([A-Z0-9/-]+)"
            invoice_match = re.search(invoice_pattern, text, re.IGNORECASE)
            if invoice_match:
                facts.append(ExtractedFact(
                    field_name="invoice_number",
                    value=invoice_match.group(1),
                    confidence=0.9,
                ))

        return facts

    def _suggest_workflow(
        self,
        document_type: DocumentType,
        extracted_facts: list[ExtractedFact],
    ) -> tuple[str | None, float]:
        """Suggest workflow based on document type and facts.

        Args:
            document_type: Classified document type
            extracted_facts: Extracted facts

        Returns:
            (suggested_workflow_name, confidence)
        """
        workflow_mappings = {
            DocumentType.SALARY_SLIP: ("labour", 0.8),
            DocumentType.TERMINATION_LETTER: ("labour", 0.9),
            DocumentType.APPOINTMENT_LETTER: ("labour", 0.7),
            DocumentType.RENT_AGREEMENT: ("tenant", 0.9),
            DocumentType.INVOICE: ("consumer", 0.7),
            DocumentType.RECEIPT: ("consumer", 0.7),
            DocumentType.WARRANTY_CARD: ("consumer", 0.8),
            DocumentType.RTI_REPLY: ("rti", 0.6),
            DocumentType.GOVERNMENT_NOTICE: ("cpgrams", 0.5),
        }

        return workflow_mappings.get(document_type, (None, 0.0))

    async def verify_extracted_facts(
        self,
        document_id: str,
        verified_facts: dict[str, Any],
    ) -> dict[str, Any]:
        """User verifies/corrects extracted facts.

        Args:
            document_id: Document identifier
            verified_facts: User-verified fact values

        Returns:
            Merged facts with verification metadata
        """
        return {
            "document_id": document_id,
            "facts": verified_facts,
            "verified_at": datetime.utcnow().isoformat(),
            "verification_method": "user_review",
        }
