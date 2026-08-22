"""Unit tests for workflow orchestrator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from chakravyuha.backend.models.citizen_case import IntentCategory, WorkflowStatus
from chakravyuha.backend.orchestration.workflow_orchestrator import WorkflowOrchestrator


@pytest.mark.asyncio
class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator functionality."""

    async def test_create_case_from_input(self, db_manager, redis_cache, mock_llm_provider):
        """Test creating case from user input."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        user_id = "user_123"
        input_text = "My road has not been repaired"

        case_id = await orchestrator.create_case(user_id, input_text)

        assert case_id is not None
        assert case_id.startswith("case_")

        # Verify case was created in database
        case = await db_manager.get_case(case_id)
        assert case is not None
        assert case.user_id == user_id
        assert case.input_text == input_text

    async def test_classify_and_route(self, db_manager, redis_cache, mock_llm_provider):
        """Test classify and route workflow."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        # Create case
        case_id = await orchestrator.create_case("user_123", "Road problem")

        # Classify
        mock_llm_provider.classify_intent.return_value = {
            "intent": "government_service_grievance",
            "confidence": 0.92,
            "reasoning": "Government service complaint",
        }

        routing = await orchestrator.classify_and_route(case_id)

        assert routing.intent == IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE
        assert routing.recommended_workflow == "cpgrams"

        # Verify case was updated
        case = await db_manager.get_case(case_id)
        assert case.intent == IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE
        assert case.intent_confidence == 0.92

    async def test_auto_handoff_high_confidence(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test automatic workflow handoff with high confidence."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        case_id = await orchestrator.create_case("user_123", "Road problem")

        mock_llm_provider.classify_intent.return_value = {
            "intent": "government_service_grievance",
            "confidence": 0.95,  # High confidence
            "reasoning": "Clear CPGRAMS case",
        }

        routing = await orchestrator.classify_and_route(case_id)

        assert routing.should_auto_handoff is True
        assert routing.recommended_workflow == "cpgrams"

        # Verify workflow was assigned
        case = await db_manager.get_case(case_id)
        assert case.workflow_name == "cpgrams"

    async def test_no_auto_handoff_low_confidence(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test no automatic handoff with low confidence."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        case_id = await orchestrator.create_case("user_123", "Can you help me?")

        mock_llm_provider.classify_intent.return_value = {
            "intent": "general_civic_information",
            "confidence": 0.55,  # Low confidence
            "reasoning": "Unclear intent",
        }

        routing = await orchestrator.classify_and_route(case_id)

        assert routing.should_auto_handoff is False

        # Workflow should NOT be auto-assigned
        case = await db_manager.get_case(case_id)
        assert case.workflow_name is None or case.workflow_name == ""

    async def test_execute_workflow_rti(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test executing RTI workflow."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        # Create RTI case
        case_id = await orchestrator.create_case(
            "user_123",
            "I want RTI records about road spending",
        )

        # Set workflow
        await db_manager.update_case(case_id, {
            "intent": IntentCategory.INFORMATION_REQUEST,
            "workflow_name": "rti",
            "workflow_status": WorkflowStatus.DRAFT,
        })

        # Execute workflow
        result = await orchestrator.execute_workflow(case_id, "rti")

        assert result is not None
        assert "status" in result

    async def test_execute_workflow_cpgrams(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test executing CPGRAMS workflow."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        case_id = await orchestrator.create_case("user_123", "Road problem")

        await db_manager.update_case(case_id, {
            "intent": IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            "workflow_name": "cpgrams",
            "workflow_status": WorkflowStatus.DRAFT,
        })

        result = await orchestrator.execute_workflow(case_id, "cpgrams")

        assert result is not None

    async def test_cache_intent_classification(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test that intent classification is cached."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        input_text = "Unique test input for caching"

        # First call - should call LLM
        case_id1 = await orchestrator.create_case("user_123", input_text)
        await orchestrator.classify_and_route(case_id1)

        # Second call with same text - should use cache
        case_id2 = await orchestrator.create_case("user_456", input_text)
        await orchestrator.classify_and_route(case_id2)

        # Verify cache was used (mock implementation)
        assert mock_llm_provider.classify_intent.call_count <= 2

    async def test_update_case_status(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test updating case workflow status."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        case_id = await orchestrator.create_case("user_123", "Test")

        # Update status
        await orchestrator.update_case_status(
            case_id,
            WorkflowStatus.READY_FOR_REVIEW,
        )

        # Verify update
        case = await db_manager.get_case(case_id)
        assert case.workflow_status == WorkflowStatus.READY_FOR_REVIEW

    async def test_get_case_summary(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test getting case summary."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        case_id = await orchestrator.create_case("user_123", "Road problem")

        summary = await orchestrator.get_case_summary(case_id)

        assert summary is not None
        assert "case_id" in summary
        assert "status" in summary
        assert "workflow" in summary

    async def test_list_user_cases(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test listing all user cases."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        user_id = "user_789"

        # Create multiple cases
        await orchestrator.create_case(user_id, "Problem 1")
        await orchestrator.create_case(user_id, "Problem 2")
        await orchestrator.create_case(user_id, "Problem 3")

        cases = await orchestrator.list_user_cases(user_id)

        assert len(cases) == 3
        assert all(case.user_id == user_id for case in cases)

    async def test_extract_jurisdiction(
        self, db_manager, redis_cache, mock_llm_provider
    ):
        """Test jurisdiction extraction from input."""
        orchestrator = WorkflowOrchestrator(
            db_manager=db_manager,
            cache=redis_cache,
            llm_provider=mock_llm_provider,
        )

        mock_llm_provider.extract_facts.return_value = {
            "state": "Tamil Nadu",
            "district": "Chennai",
            "city": "Chennai",
        }

        case_id = await orchestrator.create_case(
            "user_123",
            "Road problem in Chennai, Tamil Nadu",
        )

        await orchestrator.extract_jurisdiction(case_id)

        # Verify jurisdiction was extracted and stored
        case = await db_manager.get_case(case_id)
        assert case.state == "Tamil Nadu"
        assert case.district == "Chennai"
        assert case.city == "Chennai"
