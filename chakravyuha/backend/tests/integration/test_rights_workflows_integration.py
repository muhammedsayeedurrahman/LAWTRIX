"""Integration tests for Consumer, Tenant, and Labour rights workflows.

Tests complete workflow flows for citizen rights enforcement.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.citizen_case import CitizenCase, IntentCategory, WorkflowStatus
from backend.workflows.consumer_workflow import ConsumerWorkflowHandler
from backend.workflows.tenant_workflow import TenantWorkflowHandler
from backend.workflows.labour_workflow import LabourWorkflowHandler


@pytest.mark.asyncio
class TestConsumerWorkflowIntegration:
    """Integration tests for Consumer Rights workflow."""

    @pytest.fixture
    async def consumer_handler(self):
        """Create Consumer workflow handler."""
        return ConsumerWorkflowHandler()

    @pytest.fixture
    async def sample_consumer_case(self) -> CitizenCase:
        """Create sample consumer complaint case."""
        return CitizenCase(
            case_id="consumer_int_001",
            user_input="I bought a mobile phone for Rs 25,000 from XYZ Electronics on Jan 1, 2026. It stopped working after 2 weeks. The shop refuses to replace or refund despite valid warranty.",
            intent=IntentCategory.CONSUMER_RIGHTS,
            workflow_status=WorkflowStatus.DRAFT,
            user_metadata={
                "full_name": "Amit Patel",
                "email": "amit.patel@example.com",
                "phone": "+919900112233",
                "address": "12 Gandhi Road, Ahmedabad, Gujarat",
                "pincode": "380001",
                "state": "Gujarat",
            },
            created_at=datetime.utcnow(),
        )

    async def test_complete_consumer_flow(self, consumer_handler, sample_consumer_case):
        """Test complete consumer complaint flow."""
        # Step 1: Classify consumer complaint type
        complaint_type = await consumer_handler.classify_complaint(sample_consumer_case)

        assert complaint_type is not None
        assert "defective" in complaint_type.lower() or "warranty" in complaint_type.lower()

        # Step 2: Extract transaction details
        details = await consumer_handler.extract_transaction_details(sample_consumer_case)

        assert details is not None
        assert "product_name" in details or "item" in details
        assert "amount" in details or "price" in details
        assert details.get("amount") == 25000 or "25000" in str(details)

        # Step 3: Identify applicable law/forum
        forum = await consumer_handler.identify_consumer_forum(sample_consumer_case)

        assert forum is not None
        assert "District Consumer" in forum or "State Consumer" in forum or "National Consumer" in forum
        # Rs 25,000 falls under District Consumer Forum (<= Rs 50 lakh)
        assert "District" in forum

        # Step 4: Generate complaint draft
        draft = await consumer_handler.generate_complaint_draft(sample_consumer_case)

        assert draft is not None
        assert "Consumer Protection Act" in draft
        assert "mobile phone" in draft.lower() or "defective" in draft.lower()
        assert "25,000" in draft or "25000" in draft
        assert sample_consumer_case.user_metadata["full_name"] in draft

    async def test_consumer_forum_jurisdiction(self, consumer_handler):
        """Test correct consumer forum identification based on claim amount."""
        test_cases = [
            {"amount": 25000, "expected_forum": "District"},
            {"amount": 500000, "expected_forum": "District"},
            {"amount": 7500000, "expected_forum": "State"},
            {"amount": 15000000, "expected_forum": "National"},
        ]

        for test_case in test_cases:
            case = CitizenCase(
                case_id=f"consumer_forum_{test_case['amount']}",
                user_input=f"I have a consumer complaint for Rs {test_case['amount']}",
                intent=IntentCategory.CONSUMER_RIGHTS,
                user_metadata={"state": "Maharashtra"},
            )

            # Extract details
            details = await consumer_handler.extract_transaction_details(case)
            case.extracted_facts = details

            # Identify forum
            forum = await consumer_handler.identify_consumer_forum(case)

            assert test_case["expected_forum"] in forum


@pytest.mark.asyncio
class TestTenantWorkflowIntegration:
    """Integration tests for Tenant Rights workflow."""

    @pytest.fixture
    async def tenant_handler(self):
        """Create Tenant workflow handler."""
        return TenantWorkflowHandler()

    @pytest.fixture
    async def sample_tenant_case(self) -> CitizenCase:
        """Create sample tenant dispute case."""
        return CitizenCase(
            case_id="tenant_int_001",
            user_input="My landlord is forcing me to vacate the house without notice. I have been paying rent regularly for 3 years. The property is in Mumbai, rent is Rs 20,000 per month.",
            intent=IntentCategory.TENANT_RIGHTS,
            workflow_status=WorkflowStatus.DRAFT,
            user_metadata={
                "full_name": "Sunita Desai",
                "email": "sunita.desai@example.com",
                "phone": "+919876512345",
                "address": "Flat 301, Andheri East, Mumbai, Maharashtra",
                "pincode": "400069",
                "state": "Maharashtra",
            },
            created_at=datetime.utcnow(),
        )

    async def test_complete_tenant_flow(self, tenant_handler, sample_tenant_case):
        """Test complete tenant rights workflow."""
        # Step 1: Classify tenant issue
        issue_type = await tenant_handler.classify_tenant_issue(sample_tenant_case)

        assert issue_type is not None
        assert "eviction" in issue_type.lower() or "unlawful" in issue_type.lower()

        # Step 2: Extract tenancy details
        details = await tenant_handler.extract_tenancy_details(sample_tenant_case)

        assert details is not None
        assert "duration" in details or "rent_amount" in details
        assert "Mumbai" in str(details) or "location" in details

        # Step 3: Identify applicable rent control law
        law = await tenant_handler.identify_rent_control_law(sample_tenant_case)

        assert law is not None
        assert "Maharashtra" in law
        assert "Rent Control" in law or "Tenancy" in law

        # Step 4: Generate tenant complaint
        complaint = await tenant_handler.generate_tenant_complaint(sample_tenant_case)

        assert complaint is not None
        assert "eviction" in complaint.lower()
        assert "20,000" in complaint or "20000" in complaint
        assert sample_tenant_case.user_metadata["full_name"] in complaint

    async def test_tenant_issue_classification(self, tenant_handler):
        """Test classification of various tenant issues."""
        test_cases = [
            {"input": "Landlord not returning security deposit", "expected": "deposit"},
            {"input": "No water supply in the rented flat", "expected": "maintenance"},
            {"input": "Landlord increasing rent by 200%", "expected": "rent"},
            {"input": "Being forced to leave without proper notice", "expected": "eviction"},
        ]

        for test_case in test_cases:
            case = CitizenCase(
                case_id=f"tenant_issue_{test_case['input'][:10]}",
                user_input=test_case["input"],
                intent=IntentCategory.TENANT_RIGHTS,
            )

            issue_type = await tenant_handler.classify_tenant_issue(case)

            assert issue_type is not None
            assert test_case["expected"] in issue_type.lower()


@pytest.mark.asyncio
class TestLabourWorkflowIntegration:
    """Integration tests for Labour Rights workflow."""

    @pytest.fixture
    async def labour_handler(self):
        """Create Labour workflow handler."""
        return LabourWorkflowHandler()

    @pytest.fixture
    async def sample_labour_case(self) -> CitizenCase:
        """Create sample labour dispute case."""
        return CitizenCase(
            case_id="labour_int_001",
            user_input="I was working as a software engineer at ABC Company for 2 years earning Rs 60,000 per month. They terminated me without notice and haven't paid my last 2 months salary.",
            intent=IntentCategory.LABOUR_RIGHTS,
            workflow_status=WorkflowStatus.DRAFT,
            user_metadata={
                "full_name": "Rahul Verma",
                "email": "rahul.verma@example.com",
                "phone": "+919123456789",
                "address": "Bangalore, Karnataka",
                "state": "Karnataka",
            },
            created_at=datetime.utcnow(),
        )

    async def test_complete_labour_flow(self, labour_handler, sample_labour_case):
        """Test complete labour rights workflow."""
        # Step 1: Classify labour issue
        issue_type = await labour_handler.classify_labour_issue(sample_labour_case)

        assert issue_type is not None
        assert "termination" in issue_type.lower() or "salary" in issue_type.lower() or "dues" in issue_type.lower()

        # Step 2: Extract employment details
        details = await labour_handler.extract_employment_details(sample_labour_case)

        assert details is not None
        assert "designation" in details or "salary" in details or "duration" in details

        # Step 3: Identify applicable labour law
        law = await labour_handler.identify_labour_law(sample_labour_case)

        assert law is not None
        assert "Labour" in law or "Industrial" in law or "Employment" in law

        # Step 4: Identify appropriate forum/tribunal
        forum = await labour_handler.identify_labour_tribunal(sample_labour_case)

        assert forum is not None
        assert "Labour" in forum or "Industrial" in forum or "Tribunal" in forum

        # Step 5: Generate complaint draft
        complaint = await labour_handler.generate_labour_complaint(sample_labour_case)

        assert complaint is not None
        assert "termination" in complaint.lower() or "salary" in complaint.lower()
        assert "60,000" in complaint or "60000" in complaint
        assert sample_labour_case.user_metadata["full_name"] in complaint

    async def test_labour_issue_classification(self, labour_handler):
        """Test classification of various labour issues."""
        test_cases = [
            {"input": "Not paid wages for 3 months", "expected": "wage"},
            {"input": "Fired without notice period", "expected": "termination"},
            {"input": "No provident fund deduction shown", "expected": "pf"},
            {"input": "Forced to work 16 hours without overtime", "expected": "overtime"},
            {"input": "Unsafe working conditions in factory", "expected": "safety"},
        ]

        for test_case in test_cases:
            case = CitizenCase(
                case_id=f"labour_issue_{test_case['input'][:10]}",
                user_input=test_case["input"],
                intent=IntentCategory.LABOUR_RIGHTS,
            )

            issue_type = await labour_handler.classify_labour_issue(case)

            assert issue_type is not None
            assert test_case["expected"] in issue_type.lower()


@pytest.mark.asyncio
class TestWorkflowIntegration:
    """Test workflow orchestrator integration."""

    async def test_workflow_handoff(self):
        """Test automatic workflow handoff between handlers."""
        from backend.orchestration.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator()

        # Create case with consumer intent
        case = CitizenCase(
            case_id="handoff_001",
            user_input="I bought a defective product",
            intent=IntentCategory.CONSUMER_RIGHTS,
        )

        # Orchestrator should assign to consumer workflow
        assigned_workflow = orchestrator.get_workflow_handler(case.intent)

        assert isinstance(assigned_workflow, ConsumerWorkflowHandler)

        # Test with tenant intent
        tenant_case = CitizenCase(
            case_id="handoff_002",
            user_input="Landlord issue",
            intent=IntentCategory.TENANT_RIGHTS,
        )

        assigned_workflow = orchestrator.get_workflow_handler(tenant_case.intent)
        assert isinstance(assigned_workflow, TenantWorkflowHandler)

    async def test_multi_step_workflow_state_management(self, async_session: AsyncSession):
        """Test workflow state transitions across multiple steps."""
        from backend.models.automation_state import AutomationSession, AutomationStateEnum

        # Create automation session
        session = AutomationSession(
            session_id="automation_001",
            case_id="case_001",
            workflow_name="consumer_complaint",
            current_state=AutomationStateEnum.DISCOVERED,
        )

        # Transition through states
        session = session.transition_to(AutomationStateEnum.VALIDATED)
        assert session.current_state == AutomationStateEnum.VALIDATED

        session = session.transition_to(AutomationStateEnum.READY_FOR_USER_REVIEW)
        assert session.current_state == AutomationStateEnum.READY_FOR_USER_REVIEW

        session = session.transition_to(AutomationStateEnum.USER_CONFIRMED)
        assert session.current_state == AutomationStateEnum.USER_CONFIRMED

        # Verify transition history
        assert len(session.transitions) == 3
