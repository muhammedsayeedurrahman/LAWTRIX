"""Integration tests for RTI workflow end-to-end flow.

Tests complete user journey from case creation to RTI draft generation.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.citizen_case import CitizenCase, IntentCategory, WorkflowStatus
from backend.workflows.rti_workflow import RTIWorkflowHandler
from backend.services.llm_router import get_llm_router


@pytest.mark.asyncio
class TestRTIWorkflowIntegration:
    """Integration tests for complete RTI workflow."""

    @pytest.fixture
    async def rti_handler(self):
        """Create RTI workflow handler."""
        return RTIWorkflowHandler()

    @pytest.fixture
    async def sample_rti_case(self) -> CitizenCase:
        """Create sample RTI case."""
        return CitizenCase(
            case_id="rti_integration_001",
            user_input="I want to know why my building plan approval is delayed for 6 months. I applied to Pune Municipal Corporation on January 15, 2026.",
            intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            workflow_status=WorkflowStatus.DRAFT,
            user_metadata={
                "full_name": "Rajesh Kumar",
                "email": "rajesh.kumar@example.com",
                "phone": "+919876543210",
                "address": "123 MG Road, Pune, Maharashtra",
                "pincode": "411001",
            },
            created_at=datetime.utcnow(),
        )

    async def test_complete_rti_flow(self, rti_handler, sample_rti_case, async_session: AsyncSession):
        """Test complete RTI flow from case to draft."""
        # Step 1: Extract facts from user input
        facts = await rti_handler.extract_facts(sample_rti_case)

        assert facts is not None
        assert "subject" in facts
        assert "building" in facts["subject"].lower() or "plan" in facts["subject"].lower()
        assert "location" in facts or "authority" in facts

        # Update case with extracted facts
        sample_rti_case.extracted_facts = facts

        # Step 2: Resolve authority (CPIO)
        authority_result = await rti_handler.resolve_authority(sample_rti_case)

        assert authority_result is not None
        assert "authority_name" in authority_result
        assert "pune" in authority_result["authority_name"].lower()
        assert "cpio_name" in authority_result or "designation" in authority_result

        # Update case with authority
        sample_rti_case.authority = authority_result

        # Step 3: Generate RTI draft
        draft = await rti_handler.generate_draft(sample_rti_case)

        assert draft is not None
        assert "To," in draft or "The Central Public Information Officer" in draft
        assert "Right to Information Act, 2005" in draft
        assert "Rajesh Kumar" in draft
        assert "building plan" in draft.lower() or "approval" in draft.lower()

        # Verify draft structure
        assert "Subject:" in draft or "Sub:" in draft
        assert "Sir/Madam" in draft or "Respected" in draft

        # Update case with draft
        sample_rti_case.generated_draft = draft
        sample_rti_case.workflow_status = WorkflowStatus.READY_FOR_REVIEW

        # Step 4: Verify case is ready for submission
        assert sample_rti_case.workflow_status == WorkflowStatus.READY_FOR_REVIEW
        assert sample_rti_case.generated_draft is not None
        assert sample_rti_case.authority is not None
        assert len(sample_rti_case.generated_draft) > 200  # Substantial draft

    async def test_rti_authority_resolution_accuracy(self, rti_handler):
        """Test authority resolution for various departments."""
        test_cases = [
            {
                "input": "I need information about my PAN card application status",
                "expected_keywords": ["income tax", "tax", "pan"],
            },
            {
                "input": "Why was my passport application rejected by Regional Passport Office Mumbai?",
                "expected_keywords": ["passport", "mumbai", "regional"],
            },
            {
                "input": "I want details of road construction tender awarded in my village panchayat",
                "expected_keywords": ["panchayat", "rural", "village"],
            },
        ]

        for test_case in test_cases:
            case = CitizenCase(
                case_id=f"rti_auth_{test_case['input'][:10]}",
                user_input=test_case["input"],
                intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            )

            # Extract facts first
            facts = await rti_handler.extract_facts(case)
            case.extracted_facts = facts

            # Resolve authority
            authority = await rti_handler.resolve_authority(case)

            assert authority is not None
            assert "authority_name" in authority

            # Check if any expected keyword is in authority name
            authority_name_lower = authority["authority_name"].lower()
            keyword_found = any(
                keyword in authority_name_lower
                for keyword in test_case["expected_keywords"]
            )
            assert keyword_found, f"None of {test_case['expected_keywords']} found in {authority['authority_name']}"

    async def test_rti_draft_quality(self, rti_handler, sample_rti_case):
        """Test quality and completeness of generated RTI draft."""
        # Extract facts and resolve authority
        facts = await rti_handler.extract_facts(sample_rti_case)
        sample_rti_case.extracted_facts = facts

        authority = await rti_handler.resolve_authority(sample_rti_case)
        sample_rti_case.authority = authority

        # Generate draft
        draft = await rti_handler.generate_draft(sample_rti_case)

        # Quality checks
        required_elements = [
            "Right to Information Act, 2005",
            "Central Public Information Officer",
            "information",
            "request",
        ]

        for element in required_elements:
            assert element in draft, f"Missing required element: {element}"

        # Check user details are included
        assert sample_rti_case.user_metadata["full_name"] in draft
        assert sample_rti_case.user_metadata["address"] in draft or sample_rti_case.user_metadata["pincode"] in draft

        # Check proper formatting
        lines = draft.split("\n")
        assert len(lines) > 10  # Substantial content

        # Should have proper salutation and closing
        assert any("sir" in line.lower() or "madam" in line.lower() for line in lines[:5])
        assert any("thank" in line.lower() or "sincerely" in line.lower() for line in lines[-5:])

    async def test_rti_workflow_error_handling(self, rti_handler):
        """Test workflow handles incomplete or invalid cases gracefully."""
        # Case with minimal information
        minimal_case = CitizenCase(
            case_id="rti_minimal_001",
            user_input="I want information",
            intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
        )

        # Should still extract facts (even if limited)
        facts = await rti_handler.extract_facts(minimal_case)
        assert facts is not None

        # Should handle authority resolution even with limited info
        # May return generic or fallback authority
        authority = await rti_handler.resolve_authority(minimal_case)
        # Authority may be None or generic - that's acceptable for minimal input

    async def test_rti_multilingual_support(self, rti_handler):
        """Test RTI workflow with multilingual input."""
        # Hindi input
        hindi_case = CitizenCase(
            case_id="rti_hindi_001",
            user_input="मुझे अपने राशन कार्ड की स्थिति के बारे में जानकारी चाहिए",
            intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            user_metadata={
                "full_name": "राजेश कुमार",
                "address": "पुणे, महाराष्ट्र",
                "preferred_language": "hi",
            },
        )

        # Extract facts
        facts = await rti_handler.extract_facts(hindi_case)
        assert facts is not None

        # Should identify ration card related query
        assert "subject" in facts
        # Facts should be extracted in English for processing
        assert any(keyword in facts["subject"].lower() for keyword in ["ration", "card", "food"])


@pytest.mark.asyncio
class TestRTIWorkflowDatabaseIntegration:
    """Test RTI workflow with database persistence."""

    async def test_rti_case_persistence(self, async_session: AsyncSession):
        """Test RTI case is persisted correctly through workflow."""
        from backend.persistence.database import DatabaseManager

        db_manager = DatabaseManager()

        # Create case
        case = CitizenCase(
            case_id="rti_persist_001",
            user_input="I need information about my property tax assessment",
            intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            workflow_status=WorkflowStatus.DRAFT,
            user_metadata={
                "full_name": "Test User",
                "email": "test@example.com",
            },
        )

        # Save to database
        await db_manager.save_case(case, session=async_session)

        # Retrieve from database
        retrieved_case = await db_manager.get_case_by_id("rti_persist_001", session=async_session)

        assert retrieved_case is not None
        assert retrieved_case.case_id == case.case_id
        assert retrieved_case.user_input == case.user_input
        assert retrieved_case.intent == case.intent

        # Update case with workflow progress
        retrieved_case.extracted_facts = {"subject": "Property tax assessment"}
        retrieved_case.workflow_status = WorkflowStatus.IN_PROGRESS

        await db_manager.save_case(retrieved_case, session=async_session)

        # Verify update
        updated_case = await db_manager.get_case_by_id("rti_persist_001", session=async_session)
        assert updated_case.workflow_status == WorkflowStatus.IN_PROGRESS
        assert updated_case.extracted_facts is not None


@pytest.mark.asyncio
class TestRTIWorkflowPerformance:
    """Test RTI workflow performance and efficiency."""

    async def test_rti_workflow_execution_time(self, rti_handler, sample_rti_case):
        """Test RTI workflow completes within acceptable time."""
        import time

        start_time = time.time()

        # Execute complete flow
        facts = await rti_handler.extract_facts(sample_rti_case)
        sample_rti_case.extracted_facts = facts

        authority = await rti_handler.resolve_authority(sample_rti_case)
        sample_rti_case.authority = authority

        draft = await rti_handler.generate_draft(sample_rti_case)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete within 30 seconds (generous for LLM calls)
        assert execution_time < 30, f"RTI workflow took {execution_time}s, expected <30s"

        # Verify all outputs generated
        assert facts is not None
        assert authority is not None
        assert draft is not None
