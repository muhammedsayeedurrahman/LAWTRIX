"""Unified intent router with action-first classification.

Classifies user input into intents and routes to appropriate workflows.
Uses rule-based classification with LLM fallback for ambiguous cases.
"""

from __future__ import annotations

import re
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

from backend.models.citizen_case import IntentCategory
from backend.services.llm.router import get_llm_router


class RouteResult(BaseModel):
    """Result of intent routing."""
    model_config = ConfigDict(frozen=True)

    intent: IntentCategory
    confidence: float  # 0.0 to 1.0
    reasoning: str
    workflow: str | None = None  # Target workflow name
    auto_handoff: bool = False  # True if confidence >= 0.75
    clarification_needed: bool = False
    suggested_questions: list[str] = Field(default_factory=list)


class UnifiedIntentRouter:
    """Action-first intent classification with automatic workflow routing."""

    # Intent to workflow mapping
    INTENT_WORKFLOW_MAP = {
        IntentCategory.INFORMATION_REQUEST: "rti",
        IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE: "cpgrams",
        IntentCategory.SCHEME_ELIGIBILITY: "schemes",
        IntentCategory.RIGHTS_GUIDANCE_CONSUMER: "consumer",
        IntentCategory.RIGHTS_GUIDANCE_TENANT: "tenant",
        IntentCategory.RIGHTS_GUIDANCE_LABOUR: "labour",
        IntentCategory.CRIMINAL_LEGAL_INCIDENT: "legal",
        IntentCategory.GENERAL_CIVIC_INFORMATION: "guidance",
    }

    # Action signal patterns for rule-based classification
    ACTION_PATTERNS = {
        IntentCategory.INFORMATION_REQUEST: [
            r"\b(want|need|get|request|asking for)\s+(records?|information|documents?|data|details)\b",
            r"\brti\b",
            r"\b(public|government)\s+records?\b",
            r"\bhow much\s+(spent|sanctioned|allocated)\b",
            r"\bbudget|expenditure|funds?\b",
            r"\bshow\s+me\s+(records?|documents?)\b",
        ],
        IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE: [
            r"\b(complaint|grievance|problem|issue)\b.{0,50}\b(government|municipal|civic|public)\b",
            r"\b(road|water|electricity|garbage|drainage)\b.{0,30}\b(not|hasn't|hasn't|broken|damaged|poor)\b",
            r"\bcpgrams\b",
            r"\bfile\s+(a\s+)?complaint\b",
            r"\brepair|fix|maintain\b.{0,30}\b(road|street|drain|light)\b",
            r"\bmunicipality|corporation|panchayat\b.{0,50}\b(not|hasn't|failed)\b",
        ],
        IntentCategory.SCHEME_ELIGIBILITY: [
            r"\b(eligible|qualify|apply)\b.{0,30}\b(scheme|benefit|subsidy|pension)\b",
            r"\b(government|central|state)\s+scheme\b",
            r"\bpm-sym|pmsby|pmjjby|ayushman|kusum\b",
            r"\bpension|insurance|health\s+scheme\b",
            r"\bam\s+i\s+eligible\b",
            r"\bwhat\s+schemes?\b",
        ],
        IntentCategory.RIGHTS_GUIDANCE_TENANT: [
            r"\b(landlord|tenant|rent|deposit)\b",
            r"\beviction|lease|rental\s+agreement\b",
            r"\bsecurity\s+deposit\b.{0,30}\b(not|hasn't|won't|refused)\s+(return|refund)\b",
            r"\brent\s+(control|increase|dispute)\b",
            r"\bmaintenance|repairs?\b.{0,30}\brental\s+property\b",
        ],
        IntentCategory.RIGHTS_GUIDANCE_CONSUMER: [
            r"\b(defective|faulty|broken)\s+(product|phone|laptop|appliance)\b",
            r"\b(seller|shop|company|manufacturer)\b.{0,40}\b(refund|return|replace|warranty)\b",
            r"\bconsumer\s+(complaint|forum|rights?)\b",
            r"\bfake|spurious|counterfeit\s+product\b",
            r"\bover-?charged|billing\s+error\b",
        ],
        IntentCategory.RIGHTS_GUIDANCE_LABOUR: [
            r"\b(salary|wages?|payment)\b.{0,30}\b(not|hasn't|unpaid|pending|delay)\b",
            r"\b(employer|company|boss)\b.{0,40}\b(fired|terminated|dismiss|layoff)\b",
            r"\bpf|provident\s+fund|esi|gratuity\b",
            r"\blabour\s+(complaint|dispute|rights?)\b",
            r"\bworking\s+hours|overtime|leave\b.{0,30}\b(denied|not\s+paid)\b",
        ],
        IntentCategory.CRIMINAL_LEGAL_INCIDENT: [
            r"\b(assault|attack|hit|beat|murder|kill)\b",
            r"\b(theft|stole|robbery|burglary|looting)\b",
            r"\b(cheat|fraud|scam|conned)\b",
            r"\bfir|police\s+(complaint|report)\b",
            r"\bipc|bns|section\s+\d+\b",
            r"\bcriminal|cognizable|non-?bailable\b",
        ],
    }

    def __init__(self):
        self.llm_router = get_llm_router()

    def route(self, user_input: str, context: dict | None = None) -> RouteResult:
        """Classify intent and determine workflow routing.

        Args:
            user_input: User's text input
            context: Optional context (language, location, previous intents)

        Returns:
            RouteResult with intent, confidence, and workflow routing
        """
        context = context or {}

        # 1. Try rule-based classification first (fast, deterministic)
        action_signals = self._extract_action_signals(user_input)

        if action_signals:
            # Have clear action signals - high confidence
            intent, confidence = action_signals
            reasoning = f"Detected action signals for {intent.value}"
            return self._build_result(intent, confidence, reasoning)

        # 2. Check for ambiguous or low-information input
        if self._is_low_information(user_input):
            return RouteResult(
                intent=IntentCategory.GENERAL_CIVIC_INFORMATION,
                confidence=0.5,
                reasoning="Input is too vague for automatic routing",
                workflow=None,
                auto_handoff=False,
                clarification_needed=True,
                suggested_questions=[
                    "Tell me what happened or what you need help with",
                    "What problem are you facing?",
                    "What would you like to accomplish?",
                ],
            )

        # 3. Fall back to LLM classification for ambiguous cases
        intent, confidence, reasoning = self._llm_classify(user_input, context)
        return self._build_result(intent, confidence, reasoning)

    def _extract_action_signals(
        self,
        text: str
    ) -> tuple[IntentCategory, float] | None:
        """Extract action signals using regex patterns.

        Returns:
            (intent, confidence) or None if no clear signals
        """
        text_lower = text.lower()
        matches: dict[IntentCategory, int] = {}

        for intent, patterns in self.ACTION_PATTERNS.items():
            match_count = sum(
                1 for pattern in patterns
                if re.search(pattern, text_lower)
            )
            if match_count > 0:
                matches[intent] = match_count

        if not matches:
            return None

        # Get intent with most matches
        best_intent = max(matches.items(), key=lambda x: x[1])
        intent, match_count = best_intent

        # Confidence based on match count
        # 1 match = 0.75, 2+ matches = 0.9+
        confidence = min(0.75 + (match_count - 1) * 0.1, 0.95)

        return intent, confidence

    def _is_low_information(self, text: str) -> bool:
        """Check if input is too vague for automatic routing."""
        text_lower = text.lower().strip()

        # Very short input
        if len(text_lower) < 10:
            return True

        # Common vague phrases
        vague_phrases = [
            r"^(can you )?help( me)?$",
            r"^(i need )?help$",
            r"^what can you do$",
            r"^hello|hi|hey$",
            r"^i have (a )?question$",
        ]

        for pattern in vague_phrases:
            if re.match(pattern, text_lower):
                return True

        return False

    def _llm_classify(
        self,
        text: str,
        context: dict
    ) -> tuple[IntentCategory, float, str]:
        """Classify using LLM for ambiguous cases.

        Returns:
            (intent, confidence, reasoning)
        """
        prompt = self._build_classification_prompt(text, context)

        try:
            response = self.llm_router.generate(
                prompt=prompt,
                temperature=0.2,  # Low temperature for consistency
                max_tokens=200,
            )

            # Parse LLM response
            intent, confidence, reasoning = self._parse_llm_response(response)
            return intent, confidence, reasoning

        except Exception as e:
            print(f"LLM classification error: {e}")
            # Fall back to general civic information
            return (
                IntentCategory.GENERAL_CIVIC_INFORMATION,
                0.5,
                f"Classification error: {str(e)}"
            )

    def _build_classification_prompt(self, text: str, context: dict) -> str:
        """Build prompt for LLM classification."""
        return f"""Classify the following user input into ONE of these intents:

1. INFORMATION_REQUEST - User wants public records, RTI, government data
2. GOVERNMENT_SERVICE_GRIEVANCE - Complaint about government services (roads, water, etc.)
3. SCHEME_ELIGIBILITY - Asking about government schemes, benefits, eligibility
4. RIGHTS_GUIDANCE_CONSUMER - Consumer complaint, defective product, refund
5. RIGHTS_GUIDANCE_TENANT - Tenant rights, rent dispute, deposit, eviction
6. RIGHTS_GUIDANCE_LABOUR - Salary, termination, PF, labour rights
7. CRIMINAL_LEGAL_INCIDENT - Crime, FIR, assault, theft, fraud
8. GENERAL_CIVIC_INFORMATION - General question, unclear intent

User Input: "{text}"

Context: {context}

Respond in this EXACT format:
INTENT: <one of the 8 intents above>
CONFIDENCE: <number between 0.0 and 1.0>
REASONING: <brief explanation>"""

    def _parse_llm_response(
        self,
        response: str
    ) -> tuple[IntentCategory, float, str]:
        """Parse LLM classification response."""
        lines = response.strip().split("\n")
        intent_str = ""
        confidence = 0.5
        reasoning = ""

        for line in lines:
            if line.startswith("INTENT:"):
                intent_str = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except ValueError:
                    confidence = 0.5
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()

        # Map intent string to enum
        intent_map = {
            "INFORMATION_REQUEST": IntentCategory.INFORMATION_REQUEST,
            "GOVERNMENT_SERVICE_GRIEVANCE": IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            "SCHEME_ELIGIBILITY": IntentCategory.SCHEME_ELIGIBILITY,
            "RIGHTS_GUIDANCE_CONSUMER": IntentCategory.RIGHTS_GUIDANCE_CONSUMER,
            "RIGHTS_GUIDANCE_TENANT": IntentCategory.RIGHTS_GUIDANCE_TENANT,
            "RIGHTS_GUIDANCE_LABOUR": IntentCategory.RIGHTS_GUIDANCE_LABOUR,
            "CRIMINAL_LEGAL_INCIDENT": IntentCategory.CRIMINAL_LEGAL_INCIDENT,
            "GENERAL_CIVIC_INFORMATION": IntentCategory.GENERAL_CIVIC_INFORMATION,
        }

        intent = intent_map.get(
            intent_str,
            IntentCategory.GENERAL_CIVIC_INFORMATION
        )

        return intent, confidence, reasoning

    def _build_result(
        self,
        intent: IntentCategory,
        confidence: float,
        reasoning: str
    ) -> RouteResult:
        """Build RouteResult from classified intent."""
        workflow = self.INTENT_WORKFLOW_MAP.get(intent)
        auto_handoff = confidence >= 0.75

        return RouteResult(
            intent=intent,
            confidence=confidence,
            reasoning=reasoning,
            workflow=workflow,
            auto_handoff=auto_handoff,
            clarification_needed=not auto_handoff,
        )


@lru_cache(maxsize=1)
def get_intent_router() -> UnifiedIntentRouter:
    """Get singleton intent router instance."""
    return UnifiedIntentRouter()
