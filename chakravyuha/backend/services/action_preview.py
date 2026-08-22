"""Action preview system for workflow execution.

Provides detailed preview before any irreversible action with full transparency.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PreviewSeverity(str, Enum):
    """Severity level of information in preview."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DataSharingItem(BaseModel):
    """Single item of data being shared."""
    model_config = ConfigDict(frozen=True)

    field_name: str
    field_label: str
    value: Any
    sensitive: bool = Field(default=False)
    required: bool = Field(default=False)
    source: str | None = Field(None, description="Where this data came from")


class DocumentSubmission(BaseModel):
    """Document being submitted."""
    model_config = ConfigDict(frozen=True)

    document_name: str
    document_type: str
    file_size: int
    required: bool = Field(default=False)
    purpose: str | None = Field(None)


class RiskWarning(BaseModel):
    """Risk or warning about the action."""
    model_config = ConfigDict(frozen=True)

    severity: PreviewSeverity
    title: str
    message: str
    mitigation: str | None = Field(None, description="How to mitigate this risk")


class ExpectedOutcome(BaseModel):
    """Expected outcome of action."""
    model_config = ConfigDict(frozen=True)

    outcome_type: str = Field(..., description="Type of outcome (approval, rejection, hearing, etc.)")
    description: str
    timeline: str | None = Field(None, description="Expected timeline")
    next_steps: list[str] = Field(default_factory=list)


class ActionPreviewModel(BaseModel):
    """Comprehensive action preview before execution.

    Shows user exactly what will happen when action is executed.
    """
    model_config = ConfigDict(frozen=True)

    # Action identification
    action_id: str = Field(..., description="Unique action identifier")
    workflow_name: str
    action_type: str = Field(..., description="Type of action (RTI, CPGRAMS, Consumer Complaint, etc.)")

    # Target information
    target_authority: str
    target_portal: str | None = None
    filing_channel: str | None = Field(None, description="Online/Offline/Manual")

    # What will be shared
    data_sharing: list[DataSharingItem] = Field(default_factory=list)
    documents_to_submit: list[DocumentSubmission] = Field(default_factory=list)

    # Financial
    fees: str | None = None
    payment_method: str | None = None

    # Expected outcomes
    expected_outcomes: list[ExpectedOutcome] = Field(default_factory=list)

    # Risks and warnings
    risks_warnings: list[RiskWarning] = Field(default_factory=list)

    # What happens next
    immediate_next_steps: list[str] = Field(default_factory=list)
    automation_steps: list[str] = Field(default_factory=list, description="Steps automation will handle")
    user_steps: list[str] = Field(default_factory=list, description="Steps requiring user action")

    # Reversibility
    is_reversible: bool = Field(default=False)
    reversal_instructions: str | None = None

    # Compliance
    legal_basis: str | None = Field(None, description="Legal basis for action")
    privacy_notice: str | None = Field(None, description="Privacy/data protection notice")

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: datetime | None = Field(None, description="Preview expires (if data may change)")


class ActionPreviewBuilder:
    """Builder for creating comprehensive action previews."""

    def __init__(self, workflow_name: str, action_type: str):
        self.workflow_name = workflow_name
        self.action_type = action_type
        self.action_id = f"preview_{workflow_name}_{datetime.utcnow().timestamp()}"

        # Initialize collections
        self._target_authority: str | None = None
        self._target_portal: str | None = None
        self._filing_channel: str | None = None
        self._data_sharing: list[DataSharingItem] = []
        self._documents: list[DocumentSubmission] = []
        self._fees: str | None = None
        self._payment_method: str | None = None
        self._expected_outcomes: list[ExpectedOutcome] = []
        self._risks_warnings: list[RiskWarning] = []
        self._immediate_steps: list[str] = []
        self._automation_steps: list[str] = []
        self._user_steps: list[str] = []
        self._is_reversible: bool = False
        self._reversal_instructions: str | None = None
        self._legal_basis: str | None = None
        self._privacy_notice: str | None = None

    def set_target(
        self,
        authority: str,
        portal: str | None = None,
        filing_channel: str | None = None,
    ) -> ActionPreviewBuilder:
        """Set target authority and portal."""
        self._target_authority = authority
        self._target_portal = portal
        self._filing_channel = filing_channel
        return self

    def add_data_sharing(
        self,
        field_name: str,
        field_label: str,
        value: Any,
        sensitive: bool = False,
        required: bool = False,
        source: str | None = None,
    ) -> ActionPreviewBuilder:
        """Add data item being shared."""
        self._data_sharing.append(DataSharingItem(
            field_name=field_name,
            field_label=field_label,
            value=value,
            sensitive=sensitive,
            required=required,
            source=source,
        ))
        return self

    def add_document(
        self,
        document_name: str,
        document_type: str,
        file_size: int,
        required: bool = False,
        purpose: str | None = None,
    ) -> ActionPreviewBuilder:
        """Add document to be submitted."""
        self._documents.append(DocumentSubmission(
            document_name=document_name,
            document_type=document_type,
            file_size=file_size,
            required=required,
            purpose=purpose,
        ))
        return self

    def set_fees(
        self,
        fees: str,
        payment_method: str | None = None,
    ) -> ActionPreviewBuilder:
        """Set fees and payment method."""
        self._fees = fees
        self._payment_method = payment_method
        return self

    def add_expected_outcome(
        self,
        outcome_type: str,
        description: str,
        timeline: str | None = None,
        next_steps: list[str] | None = None,
    ) -> ActionPreviewBuilder:
        """Add expected outcome."""
        self._expected_outcomes.append(ExpectedOutcome(
            outcome_type=outcome_type,
            description=description,
            timeline=timeline,
            next_steps=next_steps or [],
        ))
        return self

    def add_risk_warning(
        self,
        severity: PreviewSeverity,
        title: str,
        message: str,
        mitigation: str | None = None,
    ) -> ActionPreviewBuilder:
        """Add risk or warning."""
        self._risks_warnings.append(RiskWarning(
            severity=severity,
            title=title,
            message=message,
            mitigation=mitigation,
        ))
        return self

    def set_next_steps(
        self,
        immediate: list[str] | None = None,
        automation: list[str] | None = None,
        user: list[str] | None = None,
    ) -> ActionPreviewBuilder:
        """Set next steps."""
        if immediate:
            self._immediate_steps = immediate
        if automation:
            self._automation_steps = automation
        if user:
            self._user_steps = user
        return self

    def set_reversibility(
        self,
        is_reversible: bool,
        reversal_instructions: str | None = None,
    ) -> ActionPreviewBuilder:
        """Set reversibility information."""
        self._is_reversible = is_reversible
        self._reversal_instructions = reversal_instructions
        return self

    def set_legal_basis(
        self,
        legal_basis: str,
        privacy_notice: str | None = None,
    ) -> ActionPreviewBuilder:
        """Set legal basis and privacy notice."""
        self._legal_basis = legal_basis
        self._privacy_notice = privacy_notice
        return self

    def build(self) -> ActionPreviewModel:
        """Build the action preview."""
        if not self._target_authority:
            raise ValueError("Target authority must be set")

        return ActionPreviewModel(
            action_id=self.action_id,
            workflow_name=self.workflow_name,
            action_type=self.action_type,
            target_authority=self._target_authority,
            target_portal=self._target_portal,
            filing_channel=self._filing_channel,
            data_sharing=self._data_sharing,
            documents_to_submit=self._documents,
            fees=self._fees,
            payment_method=self._payment_method,
            expected_outcomes=self._expected_outcomes,
            risks_warnings=self._risks_warnings,
            immediate_next_steps=self._immediate_steps,
            automation_steps=self._automation_steps,
            user_steps=self._user_steps,
            is_reversible=self._is_reversible,
            reversal_instructions=self._reversal_instructions,
            legal_basis=self._legal_basis,
            privacy_notice=self._privacy_notice,
        )


class ActionPreviewRenderer:
    """Renders action preview in different formats."""

    @staticmethod
    def render_text(preview: ActionPreviewModel) -> str:
        """Render preview as formatted text.

        Args:
            preview: Action preview

        Returns:
            Formatted text representation
        """
        lines = []

        lines.append("=" * 70)
        lines.append(f"ACTION PREVIEW: {preview.action_type}")
        lines.append("=" * 70)
        lines.append("")

        # Target
        lines.append("TARGET AUTHORITY:")
        lines.append(f"  {preview.target_authority}")
        if preview.target_portal:
            lines.append(f"  Portal: {preview.target_portal}")
        if preview.filing_channel:
            lines.append(f"  Channel: {preview.filing_channel}")
        lines.append("")

        # Data sharing
        if preview.data_sharing:
            lines.append("DATA BEING SHARED:")
            for item in preview.data_sharing:
                sensitive_mark = " [SENSITIVE]" if item.sensitive else ""
                required_mark = " *" if item.required else ""
                lines.append(f"  • {item.field_label}{required_mark}{sensitive_mark}")
                if not item.sensitive:
                    lines.append(f"    Value: {item.value}")
                if item.source:
                    lines.append(f"    Source: {item.source}")
            lines.append("")

        # Documents
        if preview.documents_to_submit:
            lines.append("DOCUMENTS TO SUBMIT:")
            for doc in preview.documents_to_submit:
                required_mark = " *" if doc.required else ""
                lines.append(f"  • {doc.document_name}{required_mark}")
                lines.append(f"    Type: {doc.document_type}")
                lines.append(f"    Size: {doc.file_size} bytes")
                if doc.purpose:
                    lines.append(f"    Purpose: {doc.purpose}")
            lines.append("")

        # Fees
        if preview.fees:
            lines.append("FEES:")
            lines.append(f"  {preview.fees}")
            if preview.payment_method:
                lines.append(f"  Payment Method: {preview.payment_method}")
            lines.append("")

        # Expected outcomes
        if preview.expected_outcomes:
            lines.append("EXPECTED OUTCOMES:")
            for outcome in preview.expected_outcomes:
                lines.append(f"  • {outcome.description}")
                if outcome.timeline:
                    lines.append(f"    Timeline: {outcome.timeline}")
            lines.append("")

        # Risks and warnings
        if preview.risks_warnings:
            lines.append("RISKS & WARNINGS:")
            for warning in preview.risks_warnings:
                severity_icon = {
                    PreviewSeverity.INFO: "ℹ",
                    PreviewSeverity.WARNING: "⚠",
                    PreviewSeverity.CRITICAL: "❗",
                }.get(warning.severity, "•")
                lines.append(f"  {severity_icon} {warning.title}")
                lines.append(f"    {warning.message}")
                if warning.mitigation:
                    lines.append(f"    Mitigation: {warning.mitigation}")
            lines.append("")

        # What happens next
        if preview.immediate_next_steps:
            lines.append("IMMEDIATE NEXT STEPS:")
            for i, step in enumerate(preview.immediate_next_steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        if preview.automation_steps:
            lines.append("AUTOMATION WILL HANDLE:")
            for step in preview.automation_steps:
                lines.append(f"  ✓ {step}")
            lines.append("")

        if preview.user_steps:
            lines.append("YOU WILL NEED TO:")
            for step in preview.user_steps:
                lines.append(f"  • {step}")
            lines.append("")

        # Reversibility
        if preview.is_reversible:
            lines.append("REVERSIBILITY: This action can be reversed")
            if preview.reversal_instructions:
                lines.append(f"  {preview.reversal_instructions}")
        else:
            lines.append("⚠ REVERSIBILITY: This action CANNOT be reversed once submitted")
        lines.append("")

        # Legal basis
        if preview.legal_basis:
            lines.append("LEGAL BASIS:")
            lines.append(f"  {preview.legal_basis}")
            lines.append("")

        # Privacy
        if preview.privacy_notice:
            lines.append("PRIVACY NOTICE:")
            lines.append(f"  {preview.privacy_notice}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("")
        lines.append("Please review all details carefully before proceeding.")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def render_html(preview: ActionPreviewModel) -> str:
        """Render preview as HTML.

        Args:
            preview: Action preview

        Returns:
            HTML representation
        """
        # Simplified HTML template
        html = f"""
        <div class="action-preview">
            <h2>{preview.action_type}</h2>
            <div class="target">
                <h3>Target Authority</h3>
                <p>{preview.target_authority}</p>
            </div>
            <!-- Additional sections would be rendered here -->
        </div>
        """
        return html

    @staticmethod
    def render_json(preview: ActionPreviewModel) -> dict:
        """Render preview as JSON-serializable dict.

        Args:
            preview: Action preview

        Returns:
            Dict representation
        """
        return preview.model_dump(mode="json")
