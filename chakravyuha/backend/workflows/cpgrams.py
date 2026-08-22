"""CPGRAMS workflow handler.

Handles government service grievances via Centralized Public Grievance
Redress and Monitoring System (CPGRAMS). Integrates existing CPGRAMS
service with CitizenCase workflow contract.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from backend.models.citizen_case import CitizenCase
from backend.workflows.base import (
    ActionPreview,
    ExecutionResult,
    ExecutionStatus,
    PrepareResult,
    TrackingResult,
    ValidationResult,
    WorkflowHandler,
)


class CPGRAMSWorkflowHandler(WorkflowHandler):
    """CPGRAMS grievance workflow handler."""

    # Broad authority categories for CPGRAMS routing
    AUTHORITY_CATEGORIES = {
        "road": ("Ministry of Road Transport and Highways", "road_transport"),
        "water": ("Ministry of Jal Shakti / State PWD", "water_supply"),
        "electricity": ("Ministry of Power / State Electricity Board", "electricity"),
        "railway": ("Ministry of Railways", "railway"),
        "postal": ("Department of Posts", "postal"),
        "telecom": ("Department of Telecommunications", "telecom"),
        "banking": ("Ministry of Finance / RBI", "banking"),
        "education": ("Ministry of Education / State Education Dept", "education"),
        "health": ("Ministry of Health and Family Welfare", "health"),
        "police": ("Ministry of Home Affairs / State Police", "police"),
        "tax": ("Ministry of Finance / CBDT/CBIC", "tax"),
        "pension": ("Ministry of Finance / DoPPW", "pension"),
        "passport": ("Ministry of External Affairs", "passport"),
        "ration": ("Ministry of Consumer Affairs / State Food & Supplies", "ration"),
        "municipal": ("State Urban Development / Municipal Corporation", "municipal"),
    }

    @property
    def workflow_name(self) -> str:
        return "cpgrams"

    async def prepare(self, case: CitizenCase) -> PrepareResult:
        """Prepare CPGRAMS grievance workflow."""
        # Extract facts from narrative
        facts = await self.extract_facts_from_narrative(
            case.problem.facts_narrative or case.input.raw_text
        )

        # Required fields for CPGRAMS
        required_fields = [
            "complainant_name",
            "complainant_mobile",
            "complainant_email",
            "complainant_address",
            "state",
            "district",
            "pin_code",
            "ministry",  # Broad category, not exact portal value
            "subject",
            "description",
            "desired_resolution",
        ]

        # Extract known fields from case
        known_fields = {
            "complainant_name": case.profile.name,
            "complainant_mobile": getattr(case.profile, "phone", None),
            "complainant_email": getattr(case.profile, "email", None),
            "complainant_address": self._extract_address(case),
            "state": case.jurisdiction.state,
            "district": case.jurisdiction.district,
            "pin_code": case.jurisdiction.pincode,
            "subject": case.problem.summary,
            "description": case.problem.facts_narrative or case.input.raw_text,
            "desired_resolution": case.problem.requested_outcome,
            "incident_date": facts.get("incident_date"),
            "service_location": facts.get("service_location"),
            "authority_involved": facts.get("authority"),
        }

        # Filter out None values
        known_fields = {k: v for k, v in known_fields.items() if v is not None}

        # Determine ministry category
        ministry, ministry_type = self._determine_ministry(
            case.problem.summary or case.input.raw_text
        )
        if ministry:
            known_fields["ministry"] = ministry
            known_fields["ministry_type"] = ministry_type

        # Determine missing fields
        missing_fields = [f for f in required_fields if f not in known_fields]

        # Generate draft grievance
        draft = None
        if len(missing_fields) <= 3:
            draft = self._generate_grievance_draft(case, known_fields)

        return PrepareResult(
            required_fields=required_fields,
            known_fields=known_fields,
            missing_fields=missing_fields,
            warnings=self._get_warnings(known_fields),
            confidence=1.0 - (len(missing_fields) / len(required_fields)),
            authority=ministry or "Ministry/Department (to be selected on portal)",
            draft=draft,
            action_options=[
                "File grievance online via CPGRAMS portal",
                "Track existing grievance status",
                "Escalate unresolved grievance",
            ],
        )

    async def validate(self, case: CitizenCase) -> ValidationResult:
        """Validate if CPGRAMS grievance is ready."""
        prepare_result = await self.prepare(case)

        blockers = []
        warnings = []

        # Check critical fields
        if not prepare_result.known_fields.get("complainant_name"):
            blockers.append("Complainant name is required")
        if not prepare_result.known_fields.get("complainant_mobile"):
            blockers.append("Mobile number is required for OTP verification")
        if not prepare_result.known_fields.get("complainant_email"):
            blockers.append("Email is required for CPGRAMS registration")
        if not prepare_result.known_fields.get("state"):
            blockers.append("State is required")
        if not prepare_result.known_fields.get("district"):
            blockers.append("District is required")
        if not prepare_result.known_fields.get("subject"):
            blockers.append("Grievance subject/summary is required")
        if not prepare_result.known_fields.get("description"):
            blockers.append("Detailed description is required")

        # Warnings
        if not prepare_result.known_fields.get("pin_code"):
            warnings.append("PIN code helps in grievance routing")
        if not prepare_result.known_fields.get("ministry"):
            warnings.append("Ministry/department category needs to be identified")
        if not prepare_result.known_fields.get("desired_resolution"):
            warnings.append("Stating desired resolution helps authorities respond appropriately")

        ready = len(blockers) == 0

        return ValidationResult(
            ready=ready,
            blockers=blockers,
            warnings=warnings,
        )

    async def preview_action(self, case: CitizenCase) -> ActionPreview:
        """Preview CPGRAMS grievance action."""
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ActionPreview(
                target_authority="",
                action_type="CPGRAMS Grievance",
                blockers=["Cannot determine ministry - provide more details about the issue"],
                next_steps=["Describe the government service or authority involved"],
            )

        return ActionPreview(
            target_authority=prepare_result.authority,
            action_type="CPGRAMS Public Grievance",
            documents_to_submit=[
                "Supporting documents (optional but recommended)",
                "Photos/videos of issue (if applicable)",
                "Previous correspondence with department",
                "Receipts/bills/application copies",
            ],
            data_shared={
                "personal_details": "Name, mobile, email, address, state, district, PIN",
                "grievance_details": "Subject, description, location, desired resolution",
                "ministry_selection": "Ministry and department (selected on portal)",
            },
            fees="Free - no fees for filing CPGRAMS grievance",
            expected_outcome=(
                "Registration number provided immediately. "
                "Response expected within 30-60 days depending on ministry. "
                "Escalation available if unsatisfied with response."
            ),
            risks_warnings=[
                "CPGRAMS is for Central Government ministries/departments and participating State authorities",
                "Not all grievances are accepted - exclusions include sub-judice matters, RTI requests, service matters",
                "Mobile number required for OTP verification during registration",
                "Grievance can be tracked online using registration number",
                "Multiple revisions/clarifications may be requested by department",
            ],
            what_happens_next=(
                "1. Register on CPGRAMS portal (if not already registered)\\n"
                "2. Login with credentials\\n"
                "3. Select appropriate Ministry and Department from portal dropdown\\n"
                "4. Fill grievance details and upload supporting documents\\n"
                "5. Review and submit\\n"
                "6. Receive registration number\\n"
                "7. Track status periodically using registration number"
            ),
        )

    def requires_confirmation(self, case: CitizenCase) -> bool:
        """CPGRAMS grievances always require user confirmation."""
        return True

    async def execute(self, case: CitizenCase) -> ExecutionResult:
        """Execute CPGRAMS grievance filing.

        Note: CPGRAMS requires user login, OTP, CAPTCHA, and ministry selection.
        Browser automation can assist but cannot bypass security checkpoints.
        """
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message="Cannot proceed - ministry category not determined",
                error="Unable to identify appropriate ministry from description",
            )

        # Check if user confirmed
        if not case.consent.final_submission:
            return ExecutionResult(
                status=ExecutionStatus.PENDING_USER_ACTION,
                message="User confirmation required",
                next_steps=[
                    "Review grievance draft",
                    "Review ministry category",
                    "Confirm to proceed with filing",
                ],
            )

        # CPGRAMS requires several human checkpoints
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            message="Grievance draft ready. Follow these steps to file on CPGRAMS:",
            next_steps=self._get_filing_steps(prepare_result.known_fields),
        )

    async def track(self, case: CitizenCase) -> TrackingResult:
        """Track CPGRAMS grievance status."""
        if not case.submission.reference_id:
            return TrackingResult(
                current_status="Not yet filed",
                last_updated=datetime.utcnow(),
                next_check=None,
                status_history=[],
                tracking_source="File grievance first to receive registration number",
            )

        return TrackingResult(
            current_status="Filed - Track using registration number",
            last_updated=datetime.utcnow(),
            next_check=datetime.utcnow() + timedelta(days=15),
            status_history=[],
            tracking_source=(
                f"Visit https://pgportal.gov.in/Status and enter registration number: "
                f"{case.submission.reference_id}"
            ),
        )

    # ── Helper Methods ───────────────────────────────────────────────────────

    async def extract_facts_from_narrative(self, narrative: str) -> dict:
        """Extract CPGRAMS-relevant facts from narrative."""
        facts = {}

        # Extract incident date
        date_patterns = [
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, narrative)
            if match:
                facts["incident_date"] = match.group(1)
                break

        # Extract authority/department mentions
        authority_patterns = [
            r"(?:department|ministry|authority|corporation|board)\s+(?:of\s+)?(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(?:department|ministry|authority|corporation|board)",
        ]
        for pattern in authority_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                facts["authority"] = match.group(1).strip().title()
                break

        return facts

    def _extract_address(self, case: CitizenCase) -> str | None:
        """Extract full address from case."""
        parts = []
        if case.jurisdiction.locality:
            parts.append(case.jurisdiction.locality)
        if case.jurisdiction.city:
            parts.append(case.jurisdiction.city)
        if case.jurisdiction.district:
            parts.append(case.jurisdiction.district)
        if case.jurisdiction.state:
            parts.append(case.jurisdiction.state)

        return ", ".join(parts) if parts else None

    def _determine_ministry(self, text: str) -> tuple[str, str]:
        """Determine likely ministry category from issue description.

        Returns: (ministry_name, ministry_type)
        """
        text_lower = text.lower()

        for keyword, (ministry, ministry_type) in self.AUTHORITY_CATEGORIES.items():
            if keyword in text_lower:
                return ministry, ministry_type

        # Default/unknown
        return "Ministry/Department (select on portal)", "general"

    def _get_warnings(self, known_fields: dict) -> list[str]:
        """Generate warnings based on known fields."""
        warnings = []

        # Check mobile number format
        mobile = known_fields.get("complainant_mobile")
        if mobile:
            mobile_str = str(mobile).replace(" ", "").replace("-", "")
            if not re.match(r"^[6-9]\d{9}$", mobile_str):
                warnings.append(
                    "Mobile number should be a valid 10-digit Indian number starting with 6-9"
                )

        # Check email format
        email = known_fields.get("complainant_email")
        if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", str(email)):
            warnings.append("Email format may be invalid")

        return warnings

    def _generate_grievance_draft(
        self,
        case: CitizenCase,
        known_fields: dict,
    ) -> str:
        """Generate CPGRAMS grievance draft."""
        ministry = known_fields.get("ministry", "[Select ministry on portal]")
        subject = known_fields.get("subject", "[Grievance subject]")
        description = known_fields.get("description", "[Detailed description]")
        resolution = known_fields.get("desired_resolution", "Appropriate action and redressal")
        incident_date = known_fields.get("incident_date", "[Date]")

        return f"""CPGRAMS GRIEVANCE DRAFT

Ministry/Department: {ministry}

Subject: {subject}

Description:
{description}

Incident Date: {incident_date}

Location: {known_fields.get('service_location') or known_fields.get('complainant_address', '[Location]')}

Desired Resolution:
{resolution}

Complainant Details:
Name: {known_fields.get('complainant_name', '[Name]')}
Mobile: {known_fields.get('complainant_mobile', '[Mobile]')}
Email: {known_fields.get('complainant_email', '[Email]')}
Address: {known_fields.get('complainant_address', '[Address]')}
State: {known_fields.get('state', '[State]')}
District: {known_fields.get('district', '[District]')}
PIN Code: {known_fields.get('pin_code', '[PIN]')}

IMPORTANT NOTES FOR PORTAL FILING:
1. Select the exact Ministry and Department from portal dropdown (verify against issue)
2. Subject should be clear and concise (max 200 characters usually)
3. Description should be factual and specific (avoid emotional language)
4. Upload supporting documents if available
5. Do not include Aadhaar number, bank details, or passwords
6. Keep copy of registration number for tracking
"""

    def _get_filing_steps(self, known_fields: dict) -> list[str]:
        """Get step-by-step filing instructions."""
        has_account = False  # Could check from case.consent or profile

        if not has_account:
            return [
                "STEP 1: REGISTER ON CPGRAMS",
                "1. Visit https://pgportal.gov.in/Registration",
                "2. Fill registration form with:",
                f"   - Name: {known_fields.get('complainant_name', '[Your name]')}",
                f"   - Mobile: {known_fields.get('complainant_mobile', '[Your mobile]')}",
                f"   - Email: {known_fields.get('complainant_email', '[Your email]')}",
                f"   - State: {known_fields.get('state', '[Your state]')}",
                f"   - District: {known_fields.get('district', '[Your district]')}",
                "3. Solve CAPTCHA",
                "4. Submit and verify mobile OTP",
                "",
                "STEP 2: FILE GRIEVANCE",
                "5. Login to CPGRAMS with email and password",
                "6. Navigate to 'Lodge Public Grievance'",
                f"7. Select Ministry: {known_fields.get('ministry', '[Select from dropdown]')}",
                "8. Select appropriate Department",
                "9. Fill grievance details from the draft above",
                "10. Upload supporting documents (if any)",
                "11. Review all details carefully",
                "12. Submit grievance",
                "13. Note down registration number (format: DARPG/X/YYYY/NNNNN)",
                "",
                "STEP 3: TRACK STATUS",
                "14. Visit https://pgportal.gov.in/Status",
                "15. Enter registration number to check status",
                "16. Check periodically for department response",
            ]
        else:
            return [
                "STEP 1: LOGIN TO CPGRAMS",
                "1. Visit https://pgportal.gov.in",
                "2. Login with your email and password",
                "",
                "STEP 2: FILE GRIEVANCE",
                "3. Navigate to 'Lodge Public Grievance'",
                f"4. Select Ministry: {known_fields.get('ministry', '[Select from dropdown]')}",
                "5. Select appropriate Department",
                "6. Fill grievance details from the draft above",
                "7. Upload supporting documents (if any)",
                "8. Review all details carefully",
                "9. Submit grievance",
                "10. Note down registration number",
                "",
                "STEP 3: TRACK STATUS",
                "11. Visit https://pgportal.gov.in/Status",
                "12. Enter registration number to check status",
            ]
