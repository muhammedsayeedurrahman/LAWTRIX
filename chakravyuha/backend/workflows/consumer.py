"""Consumer workflow handler.

Handles consumer complaints for defective products, refunds, warranties, etc.
Routes to appropriate Consumer Forum based on claim amount.
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


class ConsumerWorkflowHandler(WorkflowHandler):
    """Consumer complaint workflow handler."""

    @property
    def workflow_name(self) -> str:
        return "consumer"

    async def prepare(self, case: CitizenCase) -> PrepareResult:
        """Prepare consumer complaint workflow."""
        # Extract facts from narrative
        facts = await self.extract_facts_from_narrative(
            case.problem.facts_narrative or case.input.raw_text
        )

        # Required fields for consumer complaint
        required_fields = [
            "complainant_name",
            "complainant_address",
            "complainant_phone",
            "respondent_name",  # Seller/company
            "respondent_address",
            "product_service",
            "purchase_date",
            "purchase_amount",
            "issue_description",
            "requested_relief",
        ]

        # Extract known fields from case
        known_fields = {
            "complainant_name": case.profile.name,
            "complainant_phone": getattr(case.profile, "phone", None),
            "complainant_address": self._extract_address(case),
            "product_service": facts.get("product"),
            "purchase_amount": facts.get("amount"),
            "purchase_date": facts.get("purchase_date"),
            "respondent_name": facts.get("seller"),
            "issue_description": case.problem.summary,
            "requested_relief": case.problem.requested_outcome or "Refund/Replacement",
        }

        # Filter out None values
        known_fields = {k: v for k, v in known_fields.items() if v is not None}

        # Determine missing fields
        missing_fields = [f for f in required_fields if f not in known_fields]

        # Determine appropriate consumer forum based on amount
        authority, forum_type = self._determine_forum(
            known_fields.get("purchase_amount"),
            case.jurisdiction.state,
            case.jurisdiction.district
        )

        # Generate draft complaint if enough information
        draft = None
        if len(missing_fields) <= 3:  # Allow generating draft with a few missing fields
            draft = self._generate_complaint_draft(case, known_fields, authority)

        return PrepareResult(
            required_fields=required_fields,
            known_fields=known_fields,
            missing_fields=missing_fields,
            warnings=self._get_warnings(known_fields),
            confidence=1.0 - (len(missing_fields) / len(required_fields)),
            authority=authority,
            draft=draft,
            action_options=[
                "File complaint with Consumer Forum",
                "Send legal notice to seller/manufacturer first",
                "Approach Consumer Helpline (1800-11-4000)",
            ],
        )

    async def validate(self, case: CitizenCase) -> ValidationResult:
        """Validate if consumer complaint is ready."""
        prepare_result = await self.prepare(case)

        blockers = []
        warnings = []

        # Check critical fields
        if not prepare_result.known_fields.get("complainant_name"):
            blockers.append("Complainant name is required")
        if not prepare_result.known_fields.get("respondent_name"):
            blockers.append("Seller/company name is required")
        if not prepare_result.known_fields.get("product_service"):
            blockers.append("Product/service description is required")
        if not prepare_result.known_fields.get("issue_description"):
            blockers.append("Issue description is required")

        # Warnings
        if not prepare_result.known_fields.get("purchase_date"):
            warnings.append("Purchase date helps establish timeline")
        if not prepare_result.known_fields.get("purchase_amount"):
            warnings.append("Purchase amount determines which forum to approach")

        ready = len(blockers) == 0

        return ValidationResult(
            ready=ready,
            blockers=blockers,
            warnings=warnings,
        )

    async def preview_action(self, case: CitizenCase) -> ActionPreview:
        """Preview consumer complaint action."""
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ActionPreview(
                target_authority="",
                action_type="Consumer Complaint",
                blockers=["Cannot determine authority - purchase amount and location needed"],
                next_steps=["Provide purchase amount and your location"],
            )

        # Determine fees based on claim amount
        amount = prepare_result.known_fields.get("purchase_amount", 0)
        if isinstance(amount, str):
            amount = self._extract_amount_from_text(amount)

        fees = self._get_fees(amount)

        return ActionPreview(
            target_authority=prepare_result.authority,
            action_type="Consumer Complaint",
            documents_to_submit=[
                "Invoice/Receipt",
                "Product warranty card (if applicable)",
                "Photos/videos of defect",
                "Communication with seller (emails, messages)",
                "Complaint draft",
            ],
            data_shared={
                "complainant_details": "Name, address, phone",
                "respondent_details": "Seller/company name, address",
                "complaint_details": "Product, issue, amount, relief sought",
            },
            fees=fees,
            expected_outcome="Hearing scheduled within 90 days. Order for refund/replacement/compensation if complaint is upheld.",
            risks_warnings=[
                "Must appear for hearings (usually 2-4 hearings)",
                "Legal representation is optional but can help",
                "Appeals process available if dissatisfied with order",
                "Typical case duration: 3-6 months",
            ],
            what_happens_next=(
                "1. File complaint at Consumer Forum\n"
                "2. Forum issues notice to seller/company\n"
                "3. Seller files reply within 30 days\n"
                "4. Hearings scheduled (evidence, arguments)\n"
                "5. Forum passes order\n"
                "6. Order execution (if in your favor)"
            ),
        )

    def requires_confirmation(self, case: CitizenCase) -> bool:
        """Consumer complaints always require user confirmation."""
        return True

    async def execute(self, case: CitizenCase) -> ExecutionResult:
        """Execute consumer complaint filing.

        Note: Most consumer forums don't have online filing yet.
        This provides guidance for offline/manual filing.
        """
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message="Cannot proceed - authority not determined",
                error="Missing purchase amount or location",
            )

        # Check if user confirmed
        if not case.consent.final_submission:
            return ExecutionResult(
                status=ExecutionStatus.PENDING_USER_ACTION,
                message="User confirmation required",
                next_steps=["Review complaint draft", "Confirm to proceed"],
            )

        # Most consumer forums require offline filing
        # Provide detailed instructions
        forum_address = self._get_forum_address(
            prepare_result.authority,
            case.jurisdiction.state,
            case.jurisdiction.district
        )

        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            message="Complaint draft generated. Follow these steps to file:",
            next_steps=[
                f"1. Print complaint draft and supporting documents",
                f"2. Visit {prepare_result.authority}",
                f"   Address: {forum_address}",
                f"3. Pay filing fees (as per fee schedule)",
                f"4. Submit complaint at filing counter",
                f"5. Collect acknowledgment receipt with complaint number",
                f"6. Note next hearing date (usually given immediately)",
            ],
        )

    async def track(self, case: CitizenCase) -> TrackingResult:
        """Track consumer complaint status.

        Note: Most forums don't have online tracking.
        Returns guidance for manual tracking.
        """
        return TrackingResult(
            current_status="Filed - Manual tracking required",
            last_updated=datetime.utcnow(),
            next_check=datetime.utcnow() + timedelta(days=30),
            status_history=[],
            tracking_source=(
                "Contact Consumer Forum directly with complaint number. "
                "Online tracking not available for most forums yet."
            ),
        )

    # ── Helper Methods ───────────────────────────────────────────────────────

    async def extract_facts_from_narrative(self, narrative: str) -> dict:
        """Extract consumer complaint facts."""
        facts = {}

        # Extract product/service
        product_patterns = [
            r"(phone|laptop|tv|refrigerator|washing machine|ac|car|bike|appliance)",
            r"purchased?\s+(?:a\s+)?(\w+)",
        ]
        for pattern in product_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                facts["product"] = match.group(1)
                break

        # Extract seller/company
        seller_patterns = [
            r"from\s+(\w+(?:\s+\w+)?)",
            r"seller\s+(\w+)",
            r"company\s+(\w+)",
        ]
        for pattern in seller_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                facts["seller"] = match.group(1).strip()
                break

        # Extract amount
        amount_patterns = [
            r"(?:rs\.?|inr|rupees?)\s*(\d+(?:,\d+)*(?:\.\d+)?)",
            r"(\d+(?:,\d+)*)\s*(?:rs\.?|rupees?)",
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                amount_str = match.group(1).replace(",", "")
                facts["amount"] = float(amount_str)
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

    def _determine_forum(
        self,
        amount: float | str | None,
        state: str | None,
        district: str | None
    ) -> tuple[str, str]:
        """Determine appropriate consumer forum based on amount.

        Jurisdiction:
        - District Forum: Claims up to Rs 1 crore
        - State Forum: Claims between Rs 1 crore and Rs 10 crore
        - National Forum: Claims above Rs 10 crore
        """
        if isinstance(amount, str):
            amount = self._extract_amount_from_text(amount)

        if amount is None:
            return "Consumer Forum (amount-dependent)", "unknown"

        if amount > 10_00_00_000:  # Rs 10 crore
            return "National Consumer Disputes Redressal Commission, New Delhi", "national"
        elif amount > 1_00_00_000:  # Rs 1 crore
            state_name = state or "Your State"
            return f"State Consumer Disputes Redressal Commission, {state_name}", "state"
        else:
            district_name = district or "Your District"
            return f"District Consumer Disputes Redressal Forum, {district_name}", "district"

    def _extract_amount_from_text(self, text: str) -> float | None:
        """Extract numeric amount from text."""
        if not text:
            return None

        # Remove commas, extract numbers
        text = str(text).replace(",", "")
        match = re.search(r"\d+(?:\.\d+)?", text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    def _get_fees(self, amount: float) -> str:
        """Get filing fees based on claim amount."""
        if amount <= 1_00_000:  # Up to Rs 1 lakh
            return "Rs 100-200"
        elif amount <= 5_00_000:  # Rs 1-5 lakhs
            return "Rs 200-400"
        elif amount <= 10_00_000:  # Rs 5-10 lakhs
            return "Rs 400-600"
        elif amount <= 20_00_000:  # Rs 10-20 lakhs
            return "Rs 600-1000"
        else:
            return "Rs 1000-5000 (varies by forum)"

    def _get_warnings(self, known_fields: dict) -> list[str]:
        """Generate warnings based on known fields."""
        warnings = []

        # Check purchase date (limitation period is 2 years)
        if known_fields.get("purchase_date"):
            # TODO: Parse date and check if within limitation
            pass

        # Check if amount seems too low for forum
        amount = known_fields.get("purchase_amount")
        if amount and amount < 1000:
            warnings.append(
                "Claim amount is very low. Consider consumer helpline (1800-11-4000) first."
            )

        return warnings

    def _generate_complaint_draft(
        self,
        case: CitizenCase,
        known_fields: dict,
        authority: str
    ) -> str:
        """Generate consumer complaint draft."""
        return f"""BEFORE THE {authority.upper()}

CONSUMER COMPLAINT

In the matter of:

{known_fields.get('complainant_name', '[Your Name]')}
{known_fields.get('complainant_address', '[Your Address]')}
... Complainant

Versus

{known_fields.get('respondent_name', '[Seller/Company Name]')}
{known_fields.get('respondent_address', '[Seller Address]')}
... Opposite Party

FACTS OF THE CASE:

1. The Complainant purchased {known_fields.get('product_service', '[Product/Service]')} from the Opposite Party on {known_fields.get('purchase_date', '[Date]')} for Rs. {known_fields.get('purchase_amount', '[Amount]')}.

2. {known_fields.get('issue_description', '[Describe the defect/issue]')}.

3. Despite several requests, the Opposite Party has failed to {known_fields.get('requested_relief', 'refund/replace/repair')} the product.

4. The act of the Opposite Party amounts to deficiency in service and unfair trade practice.

PRAYER:

The Complainant respectfully prays that this Hon'ble Forum may be pleased to:

a) Direct the Opposite Party to {known_fields.get('requested_relief', 'refund the amount paid')};
b) Award compensation for mental agony and harassment;
c) Award litigation costs;
d) Pass any other order deemed fit in the interest of justice.

Place: {case.jurisdiction.city or '[City]'}
Date: {datetime.now().strftime('%d-%m-%Y')}

Signature of Complainant
{known_fields.get('complainant_name', '[Your Name]')}

DOCUMENTS ANNEXED:
1. Copy of invoice/receipt
2. Copy of warranty card (if any)
3. Photos of defect
4. Copy of complaint/communication with seller
"""

    def _get_forum_address(
        self,
        authority: str,
        state: str | None,
        district: str | None
    ) -> str:
        """Get consumer forum address.

        Note: In production, this should query a database of forum addresses.
        """
        if "National" in authority:
            return "Upbhokta Nyay Bhawan, B-1 Wing, Janpath, New Delhi - 110001"
        elif state:
            return f"[State Consumer Commission Address - {state}]"
        elif district:
            return f"[District Consumer Forum Address - {district}]"
        else:
            return "[Consumer Forum Address - Contact local consumer helpline for address]"
