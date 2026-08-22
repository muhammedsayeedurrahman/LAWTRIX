"""Labour workflow handler.

Handles employment disputes: unpaid wages, wrongful termination, PF/ESI issues,
harassment, labour law violations. Routes to appropriate labour authority.
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


class LabourWorkflowHandler(WorkflowHandler):
    """Labour/employment dispute workflow handler."""

    # Minimum wages vary by state (2026 approximate ranges)
    MIN_WAGES_RANGES = {
        "delhi": {"unskilled": 15000, "semi_skilled": 16500, "skilled": 18200},
        "maharashtra": {"unskilled": 13500, "semi_skilled": 14800, "skilled": 16200},
        "karnataka": {"unskilled": 12800, "semi_skilled": 14100, "skilled": 15500},
        "tamil nadu": {"unskilled": 11500, "semi_skilled": 12800, "skilled": 14200},
        # Default for other states
        "default": {"unskilled": 10000, "semi_skilled": 11500, "skilled": 13000},
    }

    @property
    def workflow_name(self) -> str:
        return "labour"

    async def prepare(self, case: CitizenCase) -> PrepareResult:
        """Prepare labour dispute workflow."""
        # Extract facts from narrative
        facts = await self.extract_facts_from_narrative(
            case.problem.facts_narrative or case.input.raw_text
        )

        # Required fields for labour dispute
        required_fields = [
            "employee_name",
            "employee_phone",
            "employee_address",
            "employer_name",
            "employer_address",
            "employment_start_date",
            "job_title",
            "monthly_salary",
            "issue_type",
            "issue_description",
            "state",  # Critical for jurisdiction and minimum wage
        ]

        # Extract known fields from case
        known_fields = {
            "employee_name": case.profile.name,
            "employee_phone": getattr(case.profile, "phone", None),
            "employee_address": self._extract_address(case),
            "state": case.jurisdiction.state,
            "employer_name": facts.get("employer"),
            "employment_start_date": facts.get("employment_start"),
            "job_title": facts.get("job_title"),
            "monthly_salary": facts.get("salary"),
            "unpaid_amount": facts.get("unpaid_amount"),
            "unpaid_months": facts.get("unpaid_months"),
            "issue_type": facts.get("issue_type"),
            "issue_description": case.problem.summary,
            "termination_date": facts.get("termination_date"),
            "notice_period": facts.get("notice_period"),
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
                warnings=["State is required - labour laws and authorities vary by state"],
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
            known_fields.get("monthly_salary"),
        )

        # Generate draft if enough information
        draft = None
        if len(missing_fields) <= 3:
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
                "File complaint with Labour Commissioner",
                "File case with Labour Court (for termination disputes)",
                "Approach EPFO for PF issues",
                "Approach ESIC for ESI issues",
                "File police complaint (for severe harassment/non-payment)",
                "Seek legal aid from State Legal Services Authority",
            ],
        )

    async def validate(self, case: CitizenCase) -> ValidationResult:
        """Validate if labour dispute case is ready."""
        prepare_result = await self.prepare(case)

        blockers = []
        warnings = []

        # Check critical fields
        if not prepare_result.known_fields.get("state"):
            blockers.append("State is required - labour authorities vary by state")
        if not prepare_result.known_fields.get("employee_name"):
            blockers.append("Employee name is required")
        if not prepare_result.known_fields.get("employer_name"):
            blockers.append("Employer name is required")
        if not prepare_result.known_fields.get("issue_type"):
            blockers.append("Issue type is required (wages/termination/PF/ESI/harassment)")
        if not prepare_result.known_fields.get("issue_description"):
            blockers.append("Issue description is required")

        # Warnings
        if not prepare_result.known_fields.get("employment_start_date"):
            warnings.append("Employment start date helps establish service duration")
        if not prepare_result.known_fields.get("monthly_salary"):
            warnings.append("Monthly salary is needed for wage claims and minimum wage verification")
        if not prepare_result.known_fields.get("employee_address"):
            warnings.append("Your address may be needed for jurisdiction")

        ready = len(blockers) == 0

        return ValidationResult(
            ready=ready,
            blockers=blockers,
            warnings=warnings,
        )

    async def preview_action(self, case: CitizenCase) -> ActionPreview:
        """Preview labour dispute action."""
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ActionPreview(
                target_authority="",
                action_type="Labour Dispute",
                blockers=["Cannot determine authority - state is required"],
                next_steps=["Provide your state for specific guidance"],
            )

        issue_type = prepare_result.known_fields.get("issue_type", "dispute")

        # Determine expected documents based on issue
        documents = [
            "Appointment letter / Offer letter",
            "Salary slips (last 6 months)",
            "Bank statement showing salary credits",
            "Employment contract (if any)",
            "ID proof (Aadhaar, PAN)",
        ]

        if "wage" in str(issue_type).lower() or "salary" in str(issue_type).lower():
            documents.extend([
                "Attendance records (if available)",
                "Communication regarding non-payment",
            ])
        elif "termination" in str(issue_type).lower():
            documents.extend([
                "Termination letter",
                "Service record",
                "Performance appraisals (if available)",
            ])
        elif "pf" in str(issue_type).lower():
            documents.extend([
                "UAN (Universal Account Number)",
                "Form 11 (PF nomination form)",
                "Previous PF slips",
            ])
        elif "esi" in str(issue_type).lower():
            documents.extend([
                "ESI card",
                "Medical bills/treatment records",
            ])

        # Determine fees (most labour matters have minimal/no fees)
        fees = "Usually free or nominal (Rs 50-200 for complaint filing)"

        return ActionPreview(
            target_authority=prepare_result.authority,
            action_type=f"Labour Dispute - {issue_type.replace('_', ' ').title()}",
            documents_to_submit=documents,
            data_shared={
                "employee_details": "Name, address, phone, job title",
                "employer_details": "Company name, address",
                "employment_details": "Salary, joining date, service duration",
                "dispute_details": "Issue type, unpaid amount, timeline, relief sought",
            },
            fees=fees,
            expected_outcome=self._get_expected_outcome(issue_type),
            risks_warnings=[
                "Labour proceedings may take 3-12 months depending on complexity",
                "Maintain employment relationship if possible (easier enforcement)",
                "Keep all employment records, emails, messages as evidence",
                "Many labour boards offer conciliation before formal proceedings",
                "Legal aid available from State Legal Services Authority",
                "Approach within limitation period (varies by issue: 1-3 years typically)",
            ],
            what_happens_next=self._get_next_steps(issue_type),
        )

    def requires_confirmation(self, case: CitizenCase) -> bool:
        """Labour disputes always require user confirmation."""
        return True

    async def execute(self, case: CitizenCase) -> ExecutionResult:
        """Execute labour dispute action.

        Note: Most labour authorities require offline filing or online portal-specific processes.
        This provides guidance and draft documents.
        """
        prepare_result = await self.prepare(case)

        if not prepare_result.authority:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message="Cannot proceed - state not provided",
                error="State is required to determine applicable labour laws and authority",
            )

        # Check if user confirmed
        if not case.consent.final_submission:
            return ExecutionResult(
                status=ExecutionStatus.PENDING_USER_ACTION,
                message="User confirmation required",
                next_steps=["Review complaint draft", "Confirm to proceed"],
            )

        # Most labour authorities require manual filing or state-specific portals
        issue_type = prepare_result.known_fields.get("issue_type", "dispute")

        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            message="Complaint draft generated. Follow these steps:",
            next_steps=self._get_execution_steps(
                prepare_result.authority,
                issue_type,
                prepare_result.known_fields.get("state"),
            ),
        )

    async def track(self, case: CitizenCase) -> TrackingResult:
        """Track labour dispute status.

        Note: Most cases require manual tracking.
        """
        return TrackingResult(
            current_status="Complaint filed - Manual tracking required",
            last_updated=datetime.utcnow(),
            next_check=datetime.utcnow() + timedelta(days=15),
            status_history=[],
            tracking_source=(
                "Contact Labour Commissioner office or Labour Court directly with complaint number. "
                "Some states have online portals - check your State Labour Department website."
            ),
        )

    # ── Helper Methods ───────────────────────────────────────────────────────

    async def extract_facts_from_narrative(self, narrative: str) -> dict:
        """Extract labour dispute facts."""
        facts = {}

        # Extract employer name
        employer_patterns = [
            r"employer\s+(?:is\s+)?(\w+(?:\s+\w+)?)",
            r"company\s+(?:is\s+)?(\w+(?:\s+\w+)?)",
            r"work(?:ing)?\s+(?:at|for)\s+(\w+(?:\s+\w+)?)",
        ]
        for pattern in employer_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                facts["employer"] = match.group(1).strip().title()
                break

        # Extract salary/wage amount
        salary_patterns = [
            r"salary\s+(?:of\s+)?(?:rs\.?|inr|rupees?)?\s*([\d,]+)",
            r"(?:rs\.?|inr|rupees?)\s*([\d,]+)\s+(?:per\s+)?month",
            r"earning\s+(?:rs\.?|inr|rupees?)?\s*([\d,]+)",
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                amount_str = match.group(1).replace(",", "")
                facts["salary"] = float(amount_str)
                break

        # Extract unpaid amount
        unpaid_patterns = [
            r"(?:unpaid|pending|owed?)\s+(?:salary|wages?)\s+(?:of\s+)?(?:rs\.?|inr|rupees?)?\s*([\d,]+)",
            r"(?:rs\.?|inr|rupees?)\s*([\d,]+)\s+(?:not|un)paid",
        ]
        for pattern in unpaid_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                amount_str = match.group(1).replace(",", "")
                facts["unpaid_amount"] = float(amount_str)
                break

        # Extract unpaid duration
        months_patterns = [
            r"(\d+)\s+month[s]?\s+(?:of\s+)?(?:salary|wages?)\s+(?:not|un)paid",
            r"(?:not|un)paid\s+(?:for\s+)?(\d+)\s+month",
            r"(\d+)\s+month[s]?\s+(?:salary|wages?)\s+pending",
        ]
        for pattern in months_patterns:
            match = re.search(pattern, narrative.lower())
            if match:
                facts["unpaid_months"] = int(match.group(1))
                break

        # Detect issue type
        issue_keywords = {
            "unpaid_wages": ["salary not paid", "wages not paid", "unpaid salary", "pending salary", "payment pending"],
            "wrongful_termination": ["terminated", "fired", "dismissed", "removed", "termination"],
            "pf_issue": ["pf", "provident fund", "epf", "uan"],
            "esi_issue": ["esi", "esic", "medical", "insurance"],
            "harassment": ["harass", "abuse", "discrimination", "hostile"],
            "illegal_deduction": ["deduction", "cut", "penalty"],
            "overtime": ["overtime", "extra hours", "working hours"],
            "leave_denial": ["leave", "paid leave", "casual leave"],
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
        salary: float | None,
    ) -> tuple[str, str]:
        """Determine appropriate labour authority.

        Returns: (authority_name, authority_type)
        """
        if not state:
            return "Labour authority dependent on state", "unknown"

        state_title = state.title()

        # PF issues go to EPFO
        if issue_type and "pf" in str(issue_type).lower():
            return (
                f"Employees' Provident Fund Organisation (EPFO) - {state_title} Regional Office",
                "epfo"
            )

        # ESI issues go to ESIC
        if issue_type and "esi" in str(issue_type).lower():
            return (
                f"Employees' State Insurance Corporation (ESIC) - {state_title}",
                "esic"
            )

        # Termination disputes go to Labour Court
        if issue_type and "termination" in str(issue_type).lower():
            return (
                f"Labour Court, {state_title}",
                "labour_court"
            )

        # Wage and other disputes go to Labour Commissioner
        return (
            f"Office of the Labour Commissioner, {state_title}",
            "labour_commissioner"
        )

    def _get_warnings(self, known_fields: dict) -> list[str]:
        """Generate warnings based on known fields."""
        warnings = []

        state = known_fields.get("state", "").lower()
        salary = known_fields.get("monthly_salary")

        # Check minimum wage compliance
        if state and salary:
            min_wages = self.MIN_WAGES_RANGES.get(
                state,
                self.MIN_WAGES_RANGES["default"]
            )

            if salary < min_wages["unskilled"]:
                warnings.append(
                    f"Salary appears below minimum wage for {state.title()}. "
                    f"Minimum wage violation is a serious offence."
                )

        # Check unpaid duration
        unpaid_months = known_fields.get("unpaid_months")
        if unpaid_months and unpaid_months > 3:
            warnings.append(
                f"Salary unpaid for {unpaid_months} months. "
                f"This is a criminal offence under Payment of Wages Act."
            )

        # Check employment duration for termination
        if known_fields.get("issue_type") == "wrongful_termination":
            if not known_fields.get("employment_start_date"):
                warnings.append(
                    "Employment duration affects termination rights. "
                    "Industrial Disputes Act protects workers with 1+ year service."
                )

        return warnings

    def _get_expected_outcome(self, issue_type: str | None) -> str:
        """Get expected outcome based on issue type."""
        outcomes = {
            "unpaid_wages": "Recovery of unpaid wages + 50% compensation (3-6 months)",
            "wrongful_termination": "Reinstatement with back wages OR compensation (6-18 months)",
            "pf_issue": "PF settlement + interest (2-6 months)",
            "esi_issue": "Medical reimbursement + benefits (3-6 months)",
            "harassment": "Compensation + punitive action against employer (6-12 months)",
            "illegal_deduction": "Recovery of deducted amount + penalty on employer (3-6 months)",
            "overtime": "Payment of overtime wages + compensation (3-6 months)",
            "leave_denial": "Encashment of leaves or reinstatement (2-4 months)",
        }

        if issue_type:
            for key, outcome in outcomes.items():
                if key in str(issue_type).lower():
                    return outcome

        return "Resolution through conciliation or labour court order (timeline varies)"

    def _get_next_steps(self, issue_type: str | None) -> str:
        """Get next steps based on issue type."""
        if issue_type and "pf" in str(issue_type).lower():
            return (
                "1. File grievance on EPFO Unified Portal (www.epfindia.gov.in)\\n"
                "2. Track grievance status online\\n"
                "3. EPFO issues notice to employer\\n"
                "4. Settlement or escalation to PF Commissioner"
            )
        elif issue_type and "esi" in str(issue_type).lower():
            return (
                "1. Visit nearest ESIC branch with medical documents\\n"
                "2. File claim for reimbursement/benefits\\n"
                "3. ESIC verifies claim\\n"
                "4. Settlement processed"
            )
        else:
            return (
                "1. File complaint with Labour Commissioner\\n"
                "2. Conciliation officer attempts settlement\\n"
                "3. If no settlement, case referred to Labour Court\\n"
                "4. Court hearings and evidence\\n"
                "5. Labour Court passes order\\n"
                "6. Order execution"
            )

    def _generate_complaint_draft(
        self,
        case: CitizenCase,
        known_fields: dict,
        authority: str
    ) -> str:
        """Generate labour complaint draft."""
        issue_type = known_fields.get("issue_type", "dispute")
        issue_description = known_fields.get("issue_description", "[Describe the issue]")

        # Determine relief sought based on issue type
        relief = {
            "unpaid_wages": "payment of unpaid wages with compensation",
            "wrongful_termination": "reinstatement with full back wages OR compensation",
            "pf_issue": "PF settlement with interest",
            "esi_issue": "medical reimbursement and benefits",
            "harassment": "compensation and punitive action against employer",
        }.get(issue_type, "appropriate relief")

        unpaid_amount = known_fields.get("unpaid_amount")
        unpaid_months = known_fields.get("unpaid_months")

        unpaid_details = ""
        if unpaid_amount:
            unpaid_details = f" amounting to Rs. {unpaid_amount:,.2f}"
        if unpaid_months:
            unpaid_details += f" for {unpaid_months} month(s)"

        return f"""COMPLAINT UNDER LABOUR LAWS

To:
{authority}

From:
{known_fields.get('employee_name', '[Your Name]')}
{known_fields.get('employee_address', '[Your Address]')}
Phone: {known_fields.get('employee_phone', '[Your Phone]')}

Date: {datetime.now().strftime('%d-%m-%Y')}

Subject: Complaint against {known_fields.get('employer_name', '[Employer Name]')} for {issue_type.replace('_', ' ').title()}

Respected Sir/Madam,

I hereby submit this complaint against my employer under the relevant labour laws:

COMPLAINANT DETAILS:
Name: {known_fields.get('employee_name', '[Your Name]')}
Job Title: {known_fields.get('job_title', '[Job Title]')}
Employment Start Date: {known_fields.get('employment_start_date', '[Start Date]')}
Monthly Salary: Rs. {known_fields.get('monthly_salary', '[Salary]')}

EMPLOYER DETAILS:
Company Name: {known_fields.get('employer_name', '[Employer Name]')}
Address: {known_fields.get('employer_address', '[Employer Address]')}

FACTS OF THE CASE:

1. I have been employed with the above employer since {known_fields.get('employment_start_date', '[Start Date]')} as {known_fields.get('job_title', '[Job Title]')} with a monthly salary of Rs. {known_fields.get('monthly_salary', '[Salary]')}.

2. {issue_description}

3. The employer has violated the following labour laws:
   - Payment of Wages Act, 1936 (if wage-related)
   - Industrial Disputes Act, 1947 (if termination-related)
   - Employees' Provident Funds Act, 1952 (if PF-related)
   - ESI Act, 1948 (if medical/insurance-related)

4. Despite repeated requests, the employer has failed to {relief.split()[0]} the matter.

RELIEF SOUGHT:

The complainant respectfully requests this Hon'ble Authority to:

a) Direct the employer to provide {relief};
b) Award compensation for mental agony and harassment;
c) Take punitive action against the employer for violation of labour laws;
d) Pass any other order deemed fit in the interest of justice.

DOCUMENTS ANNEXED:

1. Copy of appointment letter
2. Copy of salary slips
3. Copy of bank statement showing salary credits
4. Copy of relevant communication with employer
5. Copy of identity proof

Place: {case.jurisdiction.city or '[City]'}
Date: {datetime.now().strftime('%d-%m-%Y')}

Signature
{known_fields.get('employee_name', '[Your Name]')}

VERIFICATION:
I, {known_fields.get('employee_name', '[Your Name]')}, do hereby verify that the contents of this complaint are true and correct to the best of my knowledge and belief.

Signature
{known_fields.get('employee_name', '[Your Name]')}
"""

    def _get_execution_steps(
        self,
        authority: str,
        issue_type: str | None,
        state: str | None,
    ) -> list[str]:
        """Get execution steps for labour dispute."""
        if issue_type and "pf" in str(issue_type).lower():
            return [
                "1. Visit EPFO Unified Portal: www.epfindia.gov.in",
                "2. Login with UAN and password",
                "3. Navigate to 'Grievance' section",
                "4. File online grievance with details",
                "5. Upload supporting documents",
                "6. Submit and note grievance number",
                "7. Track status online",
            ]
        elif issue_type and "esi" in str(issue_type).lower():
            return [
                "1. Visit nearest ESIC branch",
                "2. Collect claim form",
                "3. Fill form with medical details",
                "4. Attach medical bills and reports",
                "5. Submit to ESIC officer",
                "6. Collect acknowledgment",
                "7. Follow up after 15-30 days",
            ]
        else:
            return [
                f"1. Visit {authority}",
                "2. Collect complaint form or submit typed complaint",
                "3. Attach all supporting documents",
                "4. Submit to filing counter",
                "5. Pay nominal fees (if any)",
                "6. Collect complaint number and acknowledgment",
                "7. Note conciliation date (usually within 2 weeks)",
                "8. Attend conciliation meeting",
                "9. If no settlement, case proceeds to Labour Court",
            ]
