"""Tenant workflow handler.

Handles tenant-landlord disputes: deposit, eviction, maintenance, rent increase, etc.
Routes to appropriate authority based on state and issue type.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from backend.models.citizen_case import CitizenCase, Fact
from backend.workflows.base import (
    ActionPreview,
    ExecutionResult,
    ExecutionStatus,
    PrepareResult,
    TrackingResult,
    ValidationResult,
    WorkflowHandler,
)


class TenantWorkflowHandler(WorkflowHandler):
    """Tenant-landlord dispute workflow handler."""

    # States with active Rent Control Acts (as of 2026)
    RENT_CONTROL_STATES = {
        "maharashtra": "Maharashtra Rent Control Act, 1999",
        "delhi": "Delhi Rent Control Act, 1958",
        "west bengal": "West Bengal Premises Tenancy Act, 1997",
        "tamil nadu": "Tamil Nadu Buildings (Lease and Rent Control) Act, 1960",
        "karnataka": "Karnataka Rent Control Act, 2001",
        "goa": "Goa Rent Control Act, 1968",
        "himachal pradesh": "Himachal Pradesh Urban Rent Control Act, 1987",
        "jammu and kashmir": "Jammu and Kashmir Rent Control Act, 2011",
        "uttar pradesh": "Uttar Pradesh Urban Buildings Regulation Act, 1972",
    }

    @property
    def workflow_name(self) -> str:
        return "tenant"

    async def prepare(self, case: CitizenCase) -> PrepareResult:
        """Prepare tenant dispute workflow."""
        # Extract facts from narrative
        facts = await self.extract_facts_from_narrative(
            case.problem.facts_narrative or case.input.raw_text
        )

        # Required fields for tenant dispute
        required_fields = [
            "tenant_name",
            "tenant_address",
            "tenant_phone",
            "landlord_name",
            "landlord_address",
            "property_address",
            "rental_amount",
            "deposit_amount",
            "lease_start_date",
            "issue_type",
            "issue_description",
            "state",  # Critical for jurisdiction
        ]

        # Extract known fields from case
        known_fields = {
            "tenant_name": case.profile.name,
            "tenant_phone": getattr(case.profile, "phone", None),
            "tenant_address": self._extract_address(case),
            "state": case.jurisdiction.state,
            "rental_amount": facts.get("rent"),
            "deposit_amount": facts.get("deposit"),
            "lease_start_date": facts.get("lease_date"),
            "landlord_name": facts.get("landlord"),
            "issue_type": facts.get("issue_type"),
            "issue_description": case.problem.summary,
            "property_address": facts.get("property_address"),
        }

        # Filter out None values
        known_fields = {k: v for k, v in known_fields.items() if v is not None}

        # Determine missing fields
        missing_fields = [f for f in required_fields if f not in known_fields]

        # Cannot proceed without state
        if not known_fields.get("state"):
            return PrepareResult(
                required_fields=required_fields,
                known_fields=known_fields,
                missing_fields=missing_fields,
                warnings=["State is required - rental laws vary by state"],
                confidence=0.0,
                authority=None,
                draft=None,
                action_options=[
                    "Provide your state to get specific guidance",
                ],
            )

        # Determine appropriate authority based on state and issue
        authority, authority_type = self._determine_authority(
            known_fields.get("state"),
            known_fields.get("issue_type"),
        )

        # Generate draft if enough information
        draft = None
        if len(missing_fields) <= 3:
            draft = self._generate_legal_notice_draft(case, known_fields, authority)

        return PrepareResult(
            required_fields=required_fields,
            known_fields=known_fields,
            missing_fields=missing_fields,
            warnings=self._get_warnings(known_fields),
            confidence=1.0 - (len(missing_fields) / len(required_fields)),
            authority=authority,
            draft=draft,
            action_options=[
                "Send legal notice to landlord",
                "File complaint with Rent Control Authority (if applicable)",
                "File civil suit for specific performance/damages",
                "Approach State Legal Services Authority for mediation",
            ],
        )

    async def validate(self, case: CitizenCase) -> ValidationResult:
        """Validate if tenant dispute case is ready."""
        prepare_result = await self.prepare(case)

        blockers = []
        warnings = []

        # Check critical fields
        if not prepare_result.known_fields.get("state"):
            blockers.append("State is required - rental laws vary by state")
        if not prepare_result.known_fields.get("tenant_name"):
            blockers.append("Tenant name is required")
        if not prepare_result.known_fields.get("landlord_name"):
            blockers.append("Landlord name is required")
        if not prepare_result.known_fields.get("issue_type"):
            blockers.append("Issue type is required (deposit/eviction/maintenance/etc.)")
        if not prepare_result.known_fields.get("property_address"):
            blockers.append("Property address is required")

        # Warnings
        if not prepare_result.known_fields.get("lease_start_date"):
            warnings.append("Lease start date helps establish tenancy duration")
        if not prepare_result.known_fields.get("rental_amount"):
            warnings.append("Rental amount may be needed for deposit calculation")
        if not prepare_result.known_fields.get("deposit_amount"):
            warnings.append("Deposit amount is important for refund claims")

        ready = len(blockers) == 0

        return ValidationResult(
            ready=ready,
            blockers=blockers,
            warnings=warnings,
        )

    async def preview_action(self, case: CitizenCase) -> ActionPreview:
        """Preview tenant dispute action."""
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ActionPreview(
                target_authority="",
                action_type="Tenant Dispute",
                blockers=["Cannot determine authority - state is required"],
                next_steps=["Provide your state for specific guidance"],
            )

        issue_type = prepare_result.known_fields.get("issue_type", "dispute")

        # Determine expected documents based on issue
        documents = [
            "Rent agreement/lease deed",
            "Rent receipts",
            "Deposit receipt",
        ]

        if "eviction" in str(issue_type).lower():
            documents.extend([
                "Eviction notice (if received)",
                "Communication with landlord",
            ])
        elif "deposit" in str(issue_type).lower():
            documents.extend([
                "Vacating notice/handover documents",
                "Property condition photos",
            ])
        elif "maintenance" in str(issue_type).lower():
            documents.extend([
                "Maintenance requests/complaints",
                "Photos of issues",
                "Expert reports (if available)",
            ])

        # Determine fees based on claim value
        fees = self._get_fees(
            prepare_result.known_fields.get("deposit_amount", 0),
            issue_type
        )

        return ActionPreview(
            target_authority=prepare_result.authority,
            action_type="Tenant Dispute - Legal Notice/Complaint",
            documents_to_submit=documents,
            data_shared={
                "tenant_details": "Name, address, phone",
                "landlord_details": "Name, address",
                "property_details": "Address, rent, deposit",
                "dispute_details": "Issue type, timeline, relief sought",
            },
            fees=fees,
            expected_outcome=self._get_expected_outcome(issue_type),
            risks_warnings=[
                "Legal proceedings may take 6-18 months depending on complexity",
                "Consider sending legal notice before filing suit (mandatory in some states)",
                "Mediation through Legal Services Authority is free and faster",
                "Keep paying rent to avoid counter-claim of arrears",
                "Document everything - emails, messages, photos",
            ],
            what_happens_next=self._get_next_steps(issue_type),
        )

    def requires_confirmation(self, case: CitizenCase) -> bool:
        """Tenant disputes always require user confirmation."""
        return True

    async def execute(self, case: CitizenCase) -> ExecutionResult:
        """Execute tenant dispute action.

        Note: Most tenant disputes require manual legal process.
        This provides guidance and draft documents.
        """
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message="Cannot proceed - state not provided",
                error="State is required to determine applicable laws and authority",
            )

        # Check if user confirmed
        if not case.consent.final_submission:
            return ExecutionResult(
                status=ExecutionStatus.PENDING_USER_ACTION,
                message="User confirmation required",
                next_steps=["Review legal notice draft", "Confirm to proceed"],
            )

        # Most tenant disputes require manual legal process
        issue_type = prepare_result.known_fields.get("issue_type", "dispute")

        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            message="Legal notice draft generated. Follow these steps:",
            next_steps=self._get_execution_steps(
                prepare_result.authority,
                issue_type,
                prepare_result.known_fields.get("state"),
            ),
        )

    async def track(self, case: CitizenCase) -> TrackingResult:
        """Track tenant dispute status.

        Note: Most cases require manual tracking.
        """
        return TrackingResult(
            current_status="Legal notice sent / Case filed - Manual tracking required",
            last_updated=datetime.utcnow(),
            next_check=datetime.utcnow() + timedelta(days=15),
            status_history=[],
            tracking_source=(
                "Contact Rent Control Authority or Court directly with case number. "
                "Online tracking not available for most authorities yet."
            ),
        )

    # ── Helper Methods ───────────────────────────────────────────────────────

    async def extract_facts_from_narrative(self, narrative: str) -> dict:
        """Extract tenant dispute facts."""
        facts = {}

        # Extract landlord name
        landlord_patterns = [
            r"landlord\s+(?:is\s+)?(\w+(?:\s+\w+)?)",
            r"owner\s+(?:is\s+)?(\w+(?:\s+\w+)?)",
        ]
        for pattern in landlord_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                facts["landlord"] = match.group(1).strip().title()
                break

        # Extract rental amount
        rent_patterns = [
            r"rent\s+(?:of\s+)?(?:rs\.?|inr|rupees?)?\s*([\d,]+)",
            r"(?:rs\.?|inr|rupees?)\s*([\d,]+)\s+(?:per\s+)?month",
        ]
        for pattern in rent_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                amount_str = match.group(1).replace(",", "")
                facts["rent"] = float(amount_str)
                break

        # Extract deposit amount
        deposit_patterns = [
            r"deposit\s+(?:of\s+)?(?:rs\.?|inr|rupees?)?\s*([\d,]+)",
            r"security\s+(?:deposit\s+)?(?:of\s+)?(?:rs\.?|inr|rupees?)?\s*([\d,]+)",
        ]
        for pattern in deposit_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                amount_str = match.group(1).replace(",", "")
                facts["deposit"] = float(amount_str)
                break

        # Detect issue type
        issue_keywords = {
            "deposit": ["deposit", "refund", "security", "not return"],
            "eviction": ["evict", "vacate", "remove", "leave", "notice to quit"],
            "maintenance": ["repair", "maintenance", "broken", "leaking", "damaged"],
            "rent_increase": ["increase", "raise", "hike", "more rent"],
            "harassment": ["harass", "threat", "force", "illegal entry"],
        }

        for issue_type, keywords in issue_keywords.items():
            if any(keyword in narrative.lower() for keyword in keywords):
                facts["issue_type"] = issue_type
                break

        return facts

    def _extract_address(self, case: CitizenCase) -> str | None:
        """Extract address from case."""
        parts = []
        if case.jurisdiction.city:
            parts.append(case.jurisdiction.city)
        if case.jurisdiction.district:
            parts.append(case.jurisdiction.district)
        if case.jurisdiction.state:
            parts.append(case.jurisdiction.state)
        if case.jurisdiction.pincode:
            parts.append(case.jurisdiction.pincode)

        return ", ".join(parts) if parts else None

    def _determine_authority(
        self,
        state: str | None,
        issue_type: str | None,
    ) -> tuple[str, str]:
        """Determine appropriate authority for tenant dispute.

        Returns: (authority_name, authority_type)
        """
        if not state:
            return "Authority dependent on state", "unknown"

        state_lower = state.lower()

        # Check if state has Rent Control Act
        if state_lower in self.RENT_CONTROL_STATES:
            rent_act = self.RENT_CONTROL_STATES[state_lower]

            # Eviction and rent-related issues go to Rent Controller
            if issue_type and any(
                keyword in str(issue_type).lower()
                for keyword in ["eviction", "rent", "deposit"]
            ):
                return (
                    f"Rent Control Authority, {state.title()}",
                    "rent_control"
                )

        # For states without Rent Control or other issues, go to Civil Court
        if issue_type and "eviction" in str(issue_type).lower():
            return f"Civil Court (for eviction suit), {state.title()}", "civil_court"
        elif issue_type and "deposit" in str(issue_type).lower():
            return f"Civil Court (for deposit recovery), {state.title()}", "civil_court"
        else:
            return f"Civil Court, {state.title()}", "civil_court"

    def _get_fees(self, claim_amount: float, issue_type: str | None) -> str:
        """Get filing fees estimate."""
        if not claim_amount:
            return "Rs 100-500 (for legal notice) + court fees if filing suit"

        # Court fees vary by state, rough estimates
        if claim_amount <= 50000:
            return "Rs 100-500 (legal notice) + Rs 200-1000 (court fees if applicable)"
        elif claim_amount <= 200000:
            return "Rs 500-1000 (legal notice) + Rs 1000-5000 (court fees if applicable)"
        else:
            return "Rs 1000-2000 (legal notice) + Rs 5000-15000 (court fees if applicable)"

    def _get_warnings(self, known_fields: dict) -> list[str]:
        """Generate warnings based on known fields."""
        warnings = []

        state = known_fields.get("state")
        if state and state.lower() not in self.RENT_CONTROL_STATES:
            warnings.append(
                f"{state} does not have active Rent Control Act. "
                f"You may need to file civil suit."
            )

        deposit = known_fields.get("deposit_amount")
        rent = known_fields.get("rental_amount")
        if deposit and rent and deposit > (3 * rent):
            warnings.append(
                "Deposit exceeds 3 months rent - may be recoverable even if not in agreement"
            )

        return warnings

    def _get_expected_outcome(self, issue_type: str | None) -> str:
        """Get expected outcome based on issue type."""
        outcomes = {
            "deposit": "Court order for deposit refund + interest (typically 6-12 months)",
            "eviction": "Stay on eviction or compensation (6-18 months)",
            "maintenance": "Order for repairs or rent reduction (3-6 months)",
            "rent_increase": "Stay on increase or determination of fair rent (6-12 months)",
            "harassment": "Injunction against harassment + damages (3-6 months)",
        }

        if issue_type:
            for key, outcome in outcomes.items():
                if key in str(issue_type).lower():
                    return outcome

        return "Resolution through mediation or court order (timeline varies)"

    def _get_next_steps(self, issue_type: str | None) -> str:
        """Get next steps based on issue type."""
        return (
            "1. Send legal notice to landlord (mandatory in most states)\\n"
            "2. Wait 15-30 days for landlord's response\\n"
            "3. If no resolution, file complaint/suit with appropriate authority\\n"
            "4. Authority issues notice to landlord\\n"
            "5. Both parties appear for hearings\\n"
            "6. Authority passes order\\n"
            "7. Order execution (if in your favor)"
        )

    def _generate_legal_notice_draft(
        self,
        case: CitizenCase,
        known_fields: dict,
        authority: str
    ) -> str:
        """Generate legal notice draft for tenant dispute."""
        issue_type = known_fields.get("issue_type", "dispute")
        issue_description = known_fields.get("issue_description", "[Describe the issue]")

        # Determine relief sought based on issue type
        relief = {
            "deposit": "refund the security deposit",
            "eviction": "withdraw the illegal eviction notice",
            "maintenance": "carry out necessary repairs",
            "rent_increase": "withdraw the illegal rent increase",
            "harassment": "cease harassment and illegal entry",
        }.get(issue_type, "resolve the dispute")

        return f"""LEGAL NOTICE

To:
{known_fields.get('landlord_name', '[Landlord Name]')}
{known_fields.get('landlord_address', '[Landlord Address]')}

From:
{known_fields.get('tenant_name', '[Your Name]')}
{known_fields.get('tenant_address', '[Your Address]')}

Date: {datetime.now().strftime('%d-%m-%Y')}

Subject: Legal Notice regarding tenancy dispute

Dear Sir/Madam,

Under instructions from and on behalf of my client {known_fields.get('tenant_name', '[Your Name]')}, I hereby serve you this legal notice as follows:

1. My client has been a tenant of the property situated at {known_fields.get('property_address', '[Property Address]')} since {known_fields.get('lease_start_date', '[Lease Start Date]')}, paying a monthly rent of Rs. {known_fields.get('rental_amount', '[Rent Amount]')}.

2. At the time of entering the tenancy, my client paid a security deposit of Rs. {known_fields.get('deposit_amount', '[Deposit Amount]')} to you.

3. {issue_description}

4. Despite repeated requests, you have failed to {relief}.

5. Your actions amount to breach of tenancy agreement and deficiency in service.

NOTICE:

You are hereby called upon to {relief} within 15 days from the receipt of this notice, failing which my client shall be constrained to initiate appropriate legal proceedings against you before the competent authority for recovery of the amount with interest and costs, without any further notice to you.

This notice is issued without prejudice to my client's rights and contentions, all of which are expressly reserved.

Yours faithfully,

{known_fields.get('tenant_name', '[Your Name]')}
(Tenant)

Enclosures:
1. Copy of rent agreement
2. Copy of rent receipts
3. Copy of deposit receipt
4. Copy of relevant communication
"""

    def _get_execution_steps(
        self,
        authority: str,
        issue_type: str | None,
        state: str | None,
    ) -> list[str]:
        """Get execution steps for tenant dispute."""
        steps = [
            "1. Print the legal notice on plain paper",
            "2. Send via registered post with acknowledgment to landlord",
            "3. Keep copy of notice and postal receipt",
            "4. Wait 15-30 days for landlord's response",
        ]

        if state and state.lower() in self.RENT_CONTROL_STATES:
            steps.extend([
                f"5. If no resolution, visit {authority}",
                "6. File complaint with required documents",
                "7. Pay prescribed court fees",
                "8. Collect case number and first hearing date",
            ])
        else:
            steps.extend([
                f"5. If no resolution, consult a lawyer for filing civil suit",
                f"6. File suit at appropriate Civil Court in {state}",
                "7. Follow court procedures for hearings",
            ])

        steps.append("9. Consider free mediation at State Legal Services Authority")

        return steps
