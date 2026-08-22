"""Unit tests for intent router."""

from __future__ import annotations

import pytest

from chakravyuha.backend.models.citizen_case import IntentCategory
from chakravyuha.backend.routers.intent_router import (
    IntentRouter,
    RoutingDecision,
)


@pytest.mark.asyncio
class TestIntentRouter:
    """Test IntentRouter functionality."""

    async def test_route_information_request(self, mock_llm_provider):
        """Test routing RTI/information requests."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        # Mock LLM response for RTI
        mock_llm_provider.classify_intent.return_value = {
            "intent": "information_request",
            "confidence": 0.95,
            "reasoning": "User wants government records",
        }

        decision = await router.route_intent("I want RTI records about road spending")

        assert decision.intent == IntentCategory.INFORMATION_REQUEST
        assert decision.confidence >= 0.9
        assert decision.recommended_workflow == "rti"
        assert decision.should_auto_handoff is True

    async def test_route_cpgrams_grievance(self, mock_llm_provider):
        """Test routing CPGRAMS grievances."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "government_service_grievance",
            "confidence": 0.92,
            "reasoning": "Complaint about government service",
        }

        decision = await router.route_intent("My road has not been repaired")

        assert decision.intent == IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE
        assert decision.recommended_workflow == "cpgrams"
        assert decision.should_auto_handoff is True

    async def test_route_scheme_eligibility(self, mock_llm_provider):
        """Test routing scheme eligibility queries."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "scheme_eligibility",
            "confidence": 0.88,
            "reasoning": "User asking about government schemes",
        }

        decision = await router.route_intent("What schemes am I eligible for?")

        assert decision.intent == IntentCategory.SCHEME_ELIGIBILITY
        assert decision.recommended_workflow == "schemes"

    async def test_route_tenant_rights(self, mock_llm_provider):
        """Test routing tenant rights issues."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "rights_guidance",
            "confidence": 0.90,
            "reasoning": "Tenant rights issue",
            "domain": "tenant",
        }

        decision = await router.route_intent("My landlord won't return my deposit")

        assert decision.intent == IntentCategory.RIGHTS_GUIDANCE
        assert decision.recommended_workflow == "tenant"
        assert decision.domain == "tenant"

    async def test_route_consumer_rights(self, mock_llm_provider):
        """Test routing consumer rights issues."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "rights_guidance",
            "confidence": 0.93,
            "reasoning": "Consumer protection issue",
            "domain": "consumer",
        }

        decision = await router.route_intent("Defective product, seller won't refund")

        assert decision.intent == IntentCategory.RIGHTS_GUIDANCE
        assert decision.recommended_workflow == "consumer"
        assert decision.domain == "consumer"

    async def test_route_labour_rights(self, mock_llm_provider):
        """Test routing labour rights issues."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "rights_guidance",
            "confidence": 0.91,
            "reasoning": "Labour rights issue",
            "domain": "labour",
        }

        decision = await router.route_intent("My employer hasn't paid my salary")

        assert decision.intent == IntentCategory.RIGHTS_GUIDANCE
        assert decision.recommended_workflow == "labour"
        assert decision.domain == "labour"

    async def test_route_low_confidence_no_auto_handoff(self, mock_llm_provider):
        """Test low confidence prevents auto-handoff."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "government_service_grievance",
            "confidence": 0.55,  # Low confidence
            "reasoning": "Unclear intent",
        }

        decision = await router.route_intent("Can you help me?")

        assert decision.confidence < 0.7
        assert decision.should_auto_handoff is False
        assert "clarification_needed" in decision.reasoning.lower()

    async def test_route_general_civic_info(self, mock_llm_provider):
        """Test routing general civic information queries."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "general_civic_information",
            "confidence": 0.85,
            "reasoning": "General question about civic process",
        }

        decision = await router.route_intent("What is RTI?")

        assert decision.intent == IntentCategory.GENERAL_CIVIC_INFORMATION
        assert decision.recommended_workflow is None  # No specific workflow

    async def test_route_criminal_legal(self, mock_llm_provider):
        """Test routing criminal/legal incidents."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "criminal_legal_incident",
            "confidence": 0.96,
            "reasoning": "Criminal matter requiring legal help",
        }

        decision = await router.route_intent("I was assaulted")

        assert decision.intent == IntentCategory.CRIMINAL_LEGAL_INCIDENT
        assert decision.recommended_workflow == "legal"

    async def test_routing_decision_structure(self, mock_llm_provider):
        """Test RoutingDecision contains all required fields."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.classify_intent.return_value = {
            "intent": "information_request",
            "confidence": 0.92,
            "reasoning": "RTI request",
        }

        decision = await router.route_intent("I want RTI records")

        # Verify all fields present
        assert hasattr(decision, "intent")
        assert hasattr(decision, "confidence")
        assert hasattr(decision, "recommended_workflow")
        assert hasattr(decision, "should_auto_handoff")
        assert hasattr(decision, "reasoning")
        assert hasattr(decision, "domain")
        assert hasattr(decision, "required_clarifications")

    async def test_extract_jurisdiction_from_input(self, mock_llm_provider):
        """Test jurisdiction extraction."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        mock_llm_provider.extract_facts.return_value = {
            "state": "Tamil Nadu",
            "district": "Chennai",
            "city": "Chennai",
        }

        jurisdiction = await router.extract_jurisdiction(
            "Road problem in Chennai, Tamil Nadu"
        )

        assert jurisdiction["state"] == "Tamil Nadu"
        assert jurisdiction["district"] == "Chennai"
        assert jurisdiction["city"] == "Chennai"

    async def test_confidence_threshold_customizable(self, mock_llm_provider):
        """Test custom confidence threshold."""
        router = IntentRouter(
            llm_provider=mock_llm_provider,
            confidence_threshold=0.85,
        )

        mock_llm_provider.classify_intent.return_value = {
            "intent": "government_service_grievance",
            "confidence": 0.80,  # Below custom threshold
            "reasoning": "Borderline case",
        }

        decision = await router.route_intent("Road issue")

        assert decision.should_auto_handoff is False


class TestRoutingPatterns:
    """Test common routing patterns."""

    @pytest.mark.asyncio
    async def test_road_repair_pattern(self, mock_llm_provider):
        """Test road repair routing pattern."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        test_cases = [
            "My road has potholes",
            "Road not repaired for 2 years",
            "Municipality not fixing the street",
        ]

        mock_llm_provider.classify_intent.return_value = {
            "intent": "government_service_grievance",
            "confidence": 0.92,
            "reasoning": "Government service complaint",
        }

        for text in test_cases:
            decision = await router.route_intent(text)
            assert decision.recommended_workflow == "cpgrams"

    @pytest.mark.asyncio
    async def test_rti_pattern(self, mock_llm_provider):
        """Test RTI routing pattern."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        test_cases = [
            "I want RTI records",
            "Need information about budget allocation",
            "Request for documents under RTI Act",
        ]

        mock_llm_provider.classify_intent.return_value = {
            "intent": "information_request",
            "confidence": 0.94,
            "reasoning": "Information request",
        }

        for text in test_cases:
            decision = await router.route_intent(text)
            assert decision.recommended_workflow == "rti"

    @pytest.mark.asyncio
    async def test_tenant_pattern(self, mock_llm_provider):
        """Test tenant rights routing pattern."""
        router = IntentRouter(llm_provider=mock_llm_provider)

        test_cases = [
            "Landlord won't return deposit",
            "Forced eviction issue",
            "Rent agreement dispute",
        ]

        mock_llm_provider.classify_intent.return_value = {
            "intent": "rights_guidance",
            "confidence": 0.90,
            "reasoning": "Tenant rights",
            "domain": "tenant",
        }

        for text in test_cases:
            decision = await router.route_intent(text)
            assert decision.recommended_workflow == "tenant"
            assert decision.domain == "tenant"
