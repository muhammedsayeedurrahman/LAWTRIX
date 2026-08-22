"""RTI workflow handler.

Integrates existing RTI assistant with CitizenCase workflow contract.
Handles RTI application preparation, authority routing, and filing guidance.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from backend.legal.rti_assistant import get_rti_assistant
from backend.models.citizen_case import CitizenCase
from backend.models.schemas import (
    RTIDraftRequest,
    RTIIdentifyRequest,
)
from backend.workflows.base import (
    ActionPreview,
    ExecutionResult,
    ExecutionStatus,
    PrepareResult,
    TrackingResult,
    ValidationResult,
    WorkflowHandler,
)


class RTIWorkflowHandler(WorkflowHandler):
    """RTI application workflow handler."""

    def __init__(self):
        self.rti_assistant = get_rti_assistant()

    @property
    def workflow_name(self) -> str:
        return "rti"

    async def prepare(self, case: CitizenCase) -> PrepareResult:
        """Prepare RTI application workflow."""
        # Extract jurisdiction and issue from case
        rti_request = RTIIdentifyRequest(
            issue=case.problem.summary or case.input.raw_text,
            state=case.jurisdiction.state,
            district=case.jurisdiction.district,
            city=case.jurisdiction.city,
            locality=case.jurisdiction.locality,
            authority_hint=case.jurisdiction.authority,
            road_type=None,  # Could extract from problem if needed
            date_range=None,  # Could extract from problem if needed
        )

        # Use existing RTI assistant to route
        routing = self.rti_assistant.identify_department(rti_request)

        # Generate information requests
        information_requests = self.rti_assistant.propose_information_requests(
            rti_request
        )

        # Required fields for RTI
        required_fields = [
            "applicant_name",
            "applicant_address",
            "applicant_contact",
            "is_indian_citizen",
            "issue",
            "state",
        ]

        # Extract known fields from case
        known_fields = {
            "applicant_name": case.profile.name,
            "applicant_contact": getattr(case.profile, "phone", None),
            "applicant_address": self._extract_address(case),
            "is_indian_citizen": True,  # Assume true unless specified
            "issue": case.problem.summary,
            "state": case.jurisdiction.state,
            "district": case.jurisdiction.district,
            "city": case.jurisdiction.city,
            "locality": case.jurisdiction.locality,
            "authority_hint": case.jurisdiction.authority,
            "information_requests": information_requests,
        }

        # Filter out None values
        known_fields = {k: v for k, v in known_fields.items() if v is not None}

        # Determine missing fields (combine routing + applicant requirements)
        missing_fields = list(routing.missing_information)
        if not known_fields.get("applicant_name"):
            missing_fields.append("Applicant name")
        if not known_fields.get("applicant_address"):
            missing_fields.append("Applicant postal address")

        # Generate draft if enough information
        draft = None
        if not missing_fields:
            draft_request = RTIDraftRequest(
                issue=known_fields["issue"],
                applicant_name=known_fields["applicant_name"],
                applicant_address=known_fields["applicant_address"],
                applicant_contact=known_fields.get("applicant_contact"),
                state=known_fields.get("state"),
                district=known_fields.get("district"),
                city=known_fields.get("city"),
                locality=known_fields.get("locality"),
                authority_hint=known_fields.get("authority_hint"),
                is_indian_citizen=known_fields.get("is_indian_citizen", True),
                information_requests=information_requests,
            )
            draft_response = self.rti_assistant.prepare_draft(draft_request)
            draft = draft_response.document_text

        return PrepareResult(
            required_fields=required_fields,
            known_fields=known_fields,
            missing_fields=missing_fields,
            warnings=self._get_warnings(routing, known_fields),
            confidence=float(routing.confidence.value) / 100.0,  # Convert to 0-1 scale
            authority=routing.likely_authority,
            draft=draft,
            action_options=[
                "File RTI application online (Central authorities via RTI Online)",
                "File RTI application offline (State/UT authorities)",
                "Review and edit information requests before filing",
            ],
        )

    async def validate(self, case: CitizenCase) -> ValidationResult:
        """Validate if RTI application is ready."""
        prepare_result = await self.prepare(case)

        blockers = []
        warnings = []

        # Check critical fields
        if not prepare_result.known_fields.get("applicant_name"):
            blockers.append("Applicant name is required")
        if not prepare_result.known_fields.get("applicant_address"):
            blockers.append("Applicant postal address is required")
        if not prepare_result.known_fields.get("issue"):
            blockers.append("Information request/issue is required")

        # Check jurisdiction requirements
        if not prepare_result.known_fields.get("state"):
            if not prepare_result.known_fields.get("authority_hint"):
                blockers.append(
                    "State or authority name is required to determine filing channel"
                )

        # Warnings from RTI assistant
        warnings.extend(prepare_result.warnings)

        ready = len(blockers) == 0

        return ValidationResult(
            ready=ready,
            blockers=blockers,
            warnings=warnings,
        )

    async def preview_action(self, case: CitizenCase) -> ActionPreview:
        """Preview RTI application action."""
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ActionPreview(
                target_authority="",
                action_type="RTI Application",
                blockers=["Cannot determine authority - provide state or authority name"],
                next_steps=[
                    "Provide state/UT for State authority",
                    "OR provide Central authority name",
                ],
            )

        # Get filing guidance
        rti_request = RTIIdentifyRequest(
            issue=case.problem.summary or case.input.raw_text,
            state=case.jurisdiction.state,
            authority_hint=case.jurisdiction.authority,
        )
        guidance = self.rti_assistant.filing_guidance(rti_request)

        # Determine filing channel
        filing_channel = "RTI Online portal" if guidance.pathway == "central_public_authority" else "State/UT RTI portal or offline"

        return ActionPreview(
            target_authority=prepare_result.authority,
            action_type="RTI Application",
            documents_to_submit=[
                "RTI application (generated draft)",
                "ID proof (if required by authority)",
                "BPL card copy (if claiming fee exemption)",
            ],
            data_shared={
                "applicant_details": "Name, postal address, contact (optional)",
                "information_requested": "Specific records/information sought",
                "period": "Time period for records",
                "jurisdiction": "Location/area of records",
            },
            fees="Rs 10 (Central), varies by State/UT. BPL card holders exempt.",
            expected_outcome=(
                "Information provided within 30 days (Central) or as per State RTI Act. "
                "If request transferred, additional time. "
                "First Appeal available if unsatisfied."
            ),
            risks_warnings=list(guidance.warnings),
            what_happens_next="\n".join(f"{i+1}. {step}" for i, step in enumerate(guidance.steps)),
        )

    def requires_confirmation(self, case: CitizenCase) -> bool:
        """RTI applications always require user confirmation."""
        return True

    async def execute(self, case: CitizenCase) -> ExecutionResult:
        """Execute RTI application filing.

        Note: RTI filing depends on authority type:
        - Central authorities: May use RTI Online
        - State/UT authorities: Use state portal or offline
        """
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message="Cannot proceed - authority not determined",
                error="State or authority name required",
            )

        # Check if user confirmed
        if not case.consent.final_submission:
            return ExecutionResult(
                status=ExecutionStatus.PENDING_USER_ACTION,
                message="User confirmation required",
                next_steps=[
                    "Review RTI application draft",
                    "Review information requests",
                    "Confirm applicant details",
                    "Confirm to proceed",
                ],
            )

        # Get filing guidance
        rti_request = RTIIdentifyRequest(
            issue=case.problem.summary or case.input.raw_text,
            state=case.jurisdiction.state,
            authority_hint=case.jurisdiction.authority,
        )
        guidance = self.rti_assistant.filing_guidance(rti_request)

        # Determine next steps based on pathway
        if guidance.pathway == "central_public_authority":
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                message="RTI application draft ready. File online via RTI Online portal:",
                next_steps=[
                    "1. Visit https://rtionline.gov.in",
                    "2. Register/Login to the portal",
                    "3. Select 'Submit Request' option",
                    "4. Choose the appropriate Ministry/Department",
                    "5. Fill in the details from your draft",
                    "6. Upload draft as supporting document if needed",
                    "7. Pay Rs 10 fee online",
                    "8. Submit and note registration number",
                    "9. Track status using registration number",
                ],
            )
        elif guidance.pathway == "state_or_ut_public_authority":
            state = case.jurisdiction.state or "your State/UT"
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                message=f"RTI application draft ready. File via {state} RTI portal or offline:",
                next_steps=[
                    f"1. Check {state} government RTI portal",
                    "2. If online filing available, register and submit",
                    "3. If offline filing required:",
                    "   a. Print RTI application draft",
                    "   b. Attach postal order/demand draft for fee",
                    "   c. Send via registered post to Public Information Officer",
                    "4. Keep copy and postal receipt",
                    "5. Note down submission date for tracking",
                ],
            )
        else:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message="Jurisdiction not clear",
                error="Need to determine if authority is Central or State/UT",
                next_steps=[
                    "Provide State/UT name",
                    "OR confirm Central authority name",
                ],
            )

    async def track(self, case: CitizenCase) -> TrackingResult:
        """Track RTI application status.

        Note: Tracking depends on filing channel.
        """
        # Check if filed via RTI Online (Central)
        if case.submission.reference_id and "rtionline" in str(case.submission.portal).lower():
            return TrackingResult(
                current_status="Filed via RTI Online - Track using registration number",
                last_updated=datetime.utcnow(),
                next_check=datetime.utcnow() + timedelta(days=7),
                status_history=[],
                tracking_source=(
                    "Visit https://rtionline.gov.in and use 'View Status' option "
                    "with your registration number."
                ),
            )
        else:
            # State/UT or offline filing
            return TrackingResult(
                current_status="Filed - Manual tracking required",
                last_updated=datetime.utcnow(),
                next_check=datetime.utcnow() + timedelta(days=15),
                status_history=[],
                tracking_source=(
                    "Response due within 30 days from filing. "
                    "Contact Public Information Officer if no response. "
                    "First Appeal available after 30 days or on dissatisfaction."
                ),
            )

    # ── Helper Methods ───────────────────────────────────────────────────────

    def _extract_address(self, case: CitizenCase) -> str | None:
        """Extract postal address from case."""
        parts = []
        if case.jurisdiction.locality:
            parts.append(case.jurisdiction.locality)
        if case.jurisdiction.city:
            parts.append(case.jurisdiction.city)
        if case.jurisdiction.district:
            parts.append(case.jurisdiction.district)
        if case.jurisdiction.state:
            parts.append(case.jurisdiction.state)
        if case.jurisdiction.pincode:
            parts.append(case.jurisdiction.pincode)

        return ", ".join(parts) if parts else None

    def _get_warnings(self, routing: Any, known_fields: dict) -> list[str]:
        """Get warnings from routing result and known fields."""
        warnings = []

        # Add RTI routing warnings
        if routing.status.value == "requires_verification":
            warnings.append(
                "Authority needs verification - ensure they hold the requested records"
            )

        # Check for State vs Central confusion
        state = known_fields.get("state")
        authority_hint = known_fields.get("authority_hint", "").lower()

        if state and any(term in authority_hint for term in ["central", "ministry", "government of india"]):
            warnings.append(
                "Mixed State and Central indicators - verify filing channel carefully"
            )

        # Check citizenship
        if not known_fields.get("is_indian_citizen"):
            warnings.append(
                "RTI Act 2005 requires Indian citizenship"
            )

        return warnings
