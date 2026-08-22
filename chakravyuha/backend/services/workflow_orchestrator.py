"""Enhanced orchestrator with CitizenCase and automatic workflow handoff.

Integrates intent routing, case state management, and workflow coordination.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from backend.models.citizen_case import (
    CitizenCase,
    EventType,
    IntentCategory,
    WorkflowStatus,
    create_case_from_input,
    update_case_intent,
    update_case_workflow,
)
from backend.services.intent_router import get_intent_router
from backend.services.legal_service import LegalService, get_legal_service
from backend.services.voice_service import VoiceService, get_voice_service

logger = logging.getLogger("workflow_orchestrator")


class WorkflowOrchestrator:
    """Enhanced orchestrator with CitizenCase and automatic workflow handoff."""

    def __init__(
        self,
        legal: LegalService | None = None,
        voice: VoiceService | None = None,
    ):
        self._legal = legal or get_legal_service()
        self._voice = voice or get_voice_service()
        self._intent_router = get_intent_router()

    async def process_text_input(
        self,
        text: str,
        language: str = "en-IN",
        context: dict | None = None
    ) -> tuple[CitizenCase, dict]:
        """Process text input and create/route citizen case.

        Args:
            text: User's text input
            language: Input language
            context: Optional context (previous messages, user profile)

        Returns:
            (CitizenCase, response_data)
        """
        context = context or {}

        # 1. Create initial case from input
        case = create_case_from_input(
            raw_text=text,
            language=language,
            input_method="text",
        )

        # 2. Classify intent
        route_result = self._intent_router.route(text, context)

        # 3. Update case with classified intent
        case = update_case_intent(
            case,
            category=route_result.intent,
            confidence=route_result.confidence,
            reasoning=route_result.reasoning,
        )

        # 4. Create timeline event
        timeline_event = case.to_timeline_event(
            event_type=EventType.INTENT_CLASSIFIED,
            actor="system",
            description=f"Intent classified as {route_result.intent.value}",
            details={
                "confidence": route_result.confidence,
                "reasoning": route_result.reasoning,
                "auto_handoff": route_result.auto_handoff,
            }
        )

        # 5. Automatic workflow handoff if confidence high enough
        if route_result.auto_handoff and route_result.workflow:
            case = update_case_workflow(
                case,
                workflow_name=route_result.workflow,
                status=WorkflowStatus.COLLECTING_INFO,
            )

            # Add workflow started event
            workflow_event = case.to_timeline_event(
                event_type=EventType.WORKFLOW_STARTED,
                actor="system",
                description=f"Auto-started {route_result.workflow} workflow",
                details={"intent": route_result.intent.value}
            )

            response_data = {
                "case_id": case.case_id,
                "intent": route_result.intent.value,
                "confidence": route_result.confidence,
                "workflow": route_result.workflow,
                "auto_handoff": True,
                "message": self._get_handoff_message(route_result.intent, route_result.workflow),
                "timeline": [timeline_event.model_dump(), workflow_event.model_dump()],
            }
        else:
            # Low confidence - ask for clarification
            response_data = {
                "case_id": case.case_id,
                "intent": route_result.intent.value,
                "confidence": route_result.confidence,
                "workflow": None,
                "auto_handoff": False,
                "clarification_needed": True,
                "message": "I'd be happy to help. Could you tell me more about what you need?",
                "suggested_questions": route_result.suggested_questions,
                "timeline": [timeline_event.model_dump()],
            }

        return case, response_data

    async def process_voice_input(
        self,
        audio_bytes: bytes,
        language: str | None = None,
        content_type: str = "audio/wav",
        context: dict | None = None
    ) -> tuple[CitizenCase | None, dict]:
        """Process voice input with ASR → intent → workflow routing.

        Args:
            audio_bytes: Audio file bytes
            language: Expected language (auto-detect if None)
            content_type: Audio MIME type
            context: Optional context

        Returns:
            (CitizenCase | None, response_data)
        """
        # 1. ASR (transcription)
        transcription = await self._voice.transcribe(
            audio_bytes,
            language,
            content_type=content_type
        )

        if transcription.mode == "fallback" or not transcription.text:
            return None, {
                "transcription": transcription.model_dump(),
                "message": "Could not understand audio. Please type your question instead.",
                "audio": None,
            }

        # 2. Process transcribed text
        case, response_data = await self.process_text_input(
            text=transcription.text,
            language=transcription.language,
            context=context or {},
        )

        # 3. Update case with transcript
        case = case.with_updates(
            input=case.input.model_copy(update={
                "transcript": transcription.text,
                "input_method": "voice",
            })
        )

        # 4. Add transcription to response
        response_data["transcription"] = transcription.model_dump()

        # 5. Generate TTS response (optional)
        if response_data.get("message"):
            try:
                audio_bytes_response = await self._voice.synthesize(
                    text=response_data["message"],
                    language=transcription.language,
                )
                response_data["audio_response"] = audio_bytes_response
            except Exception as e:
                logger.warning(f"TTS generation failed: {e}")
                response_data["audio_response"] = None

        return case, response_data

    def _get_handoff_message(self, intent: IntentCategory, workflow: str) -> str:
        """Get user-friendly message for workflow handoff."""
        messages = {
            IntentCategory.INFORMATION_REQUEST: "Got it. This looks like a request for public records. I'll help you prepare an RTI application.",
            IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE: "I understand. This sounds like a government service grievance. Let's prepare a complaint for CPGRAMS.",
            IntentCategory.SCHEME_ELIGIBILITY: "I can help you find government schemes you might be eligible for. Let me ask a few questions.",
            IntentCategory.RIGHTS_GUIDANCE_CONSUMER: "This appears to be a consumer complaint. I'll guide you through the process of filing it.",
            IntentCategory.RIGHTS_GUIDANCE_TENANT: "That sounds like a tenancy issue. I can help you understand your rights and prepare the next step.",
            IntentCategory.RIGHTS_GUIDANCE_LABOUR: "I understand this is a labour rights matter. Let me help you prepare the appropriate action.",
            IntentCategory.CRIMINAL_LEGAL_INCIDENT: "This seems to be a legal/criminal matter. I'll help you understand the relevant laws and next steps.",
        }
        return messages.get(
            intent,
            f"I'll help you with this. Starting {workflow} workflow."
        )

    async def continue_workflow(
        self,
        case: CitizenCase,
        user_response: str | dict,
    ) -> tuple[CitizenCase, dict]:
        """Continue an existing workflow with user's response.

        Args:
            case: Current CitizenCase
            user_response: User's response (text or structured data)

        Returns:
            (updated_case, response_data)
        """
        workflow_name = case.workflow.name

        # Route to appropriate workflow handler
        # (These will be implemented in subsequent tasks/weeks)
        if workflow_name == "rti":
            return await self._continue_rti_workflow(case, user_response)
        elif workflow_name == "cpgrams":
            return await self._continue_cpgrams_workflow(case, user_response)
        elif workflow_name == "schemes":
            return await self._continue_schemes_workflow(case, user_response)
        elif workflow_name == "consumer":
            return await self._continue_consumer_workflow(case, user_response)
        elif workflow_name == "tenant":
            return await self._continue_tenant_workflow(case, user_response)
        elif workflow_name == "labour":
            return await self._continue_labour_workflow(case, user_response)
        else:
            return case, {
                "error": f"Unknown workflow: {workflow_name}",
                "message": "This workflow is not yet implemented.",
            }

    async def _continue_rti_workflow(
        self,
        case: CitizenCase,
        user_response: str | dict
    ) -> tuple[CitizenCase, dict]:
        """Continue RTI workflow (placeholder for now)."""
        # TODO: Implement RTI workflow continuation
        # Will integrate with existing rti_assistant.py
        return case, {
            "message": "RTI workflow continuation - to be implemented",
            "next_question": "What specific records do you need?",
        }

    async def _continue_cpgrams_workflow(
        self,
        case: CitizenCase,
        user_response: str | dict
    ) -> tuple[CitizenCase, dict]:
        """Continue CPGRAMS workflow (placeholder for now)."""
        # TODO: Implement CPGRAMS workflow continuation
        # Will integrate with existing cpgrams_service.py
        return case, {
            "message": "CPGRAMS workflow continuation - to be implemented",
            "next_question": "Which government service is this complaint about?",
        }

    async def _continue_schemes_workflow(
        self,
        case: CitizenCase,
        user_response: str | dict
    ) -> tuple[CitizenCase, dict]:
        """Continue schemes workflow (placeholder for now)."""
        # TODO: Implement schemes workflow continuation
        # Will integrate with SchemeEngine
        return case, {
            "message": "Schemes workflow continuation - to be implemented",
            "next_question": "What is your age and occupation?",
        }

    async def _continue_consumer_workflow(
        self,
        case: CitizenCase,
        user_response: str | dict
    ) -> tuple[CitizenCase, dict]:
        """Continue consumer workflow (placeholder for now)."""
        # TODO: Implement consumer workflow
        return case, {
            "message": "Consumer workflow continuation - to be implemented",
        }

    async def _continue_tenant_workflow(
        self,
        case: CitizenCase,
        user_response: str | dict
    ) -> tuple[CitizenCase, dict]:
        """Continue tenant workflow (placeholder for now)."""
        # TODO: Implement tenant workflow
        return case, {
            "message": "Tenant workflow continuation - to be implemented",
        }

    async def _continue_labour_workflow(
        self,
        case: CitizenCase,
        user_response: str | dict
    ) -> tuple[CitizenCase, dict]:
        """Continue labour workflow (placeholder for now)."""
        # TODO: Implement labour workflow
        return case, {
            "message": "Labour workflow continuation - to be implemented",
        }


@lru_cache(maxsize=1)
def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get singleton workflow orchestrator instance."""
    return WorkflowOrchestrator()
