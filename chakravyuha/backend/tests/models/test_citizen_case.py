"""Unit tests for CitizenCase model."""

from __future__ import annotations

from datetime import datetime

import pytest

from chakravyuha.backend.models.citizen_case import (
    AutomationMode,
    CitizenCase,
    IntentCategory,
    WorkflowStatus,
)


class TestCitizenCaseCreation:
    """Test CitizenCase model creation and validation."""

    def test_create_minimal_case(self):
        """Test creating case with minimal required fields."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test problem",
        )

        assert case.case_id == "case_001"
        assert case.user_id == "user_123"
        assert case.input_text == "Test problem"
        assert case.intent is None
        assert case.intent_confidence == 0.0
        assert case.workflow_status == WorkflowStatus.PENDING
        assert case.automation_mode == AutomationMode.NONE
        assert isinstance(case.created_at, datetime)
        assert isinstance(case.updated_at, datetime)

    def test_create_complete_case(self, sample_citizen_case):
        """Test creating case with all fields populated."""
        case = sample_citizen_case

        assert case.case_id == "test_case_001"
        assert case.user_id == "user_123"
        assert case.input_text == "My road has not been repaired for 2 years."
        assert case.intent == IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE
        assert case.intent_confidence == 0.92
        assert case.problem_summary == "Road repair grievance"
        assert case.state == "Tamil Nadu"
        assert case.district == "Chennai"
        assert case.workflow_name == "cpgrams"
        assert case.workflow_status == "draft"

    def test_intent_categories(self):
        """Test all intent category values."""
        intents = [
            IntentCategory.INFORMATION_REQUEST,
            IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            IntentCategory.SCHEME_ELIGIBILITY,
            IntentCategory.RIGHTS_GUIDANCE,
            IntentCategory.CRIMINAL_LEGAL_INCIDENT,
            IntentCategory.GENERAL_CIVIC_INFORMATION,
        ]

        for intent in intents:
            case = CitizenCase(
                case_id=f"case_{intent.value}",
                user_id="user_123",
                input_text="Test",
                intent=intent,
            )
            assert case.intent == intent

    def test_workflow_status_values(self):
        """Test workflow status enum values."""
        statuses = [
            WorkflowStatus.PENDING,
            WorkflowStatus.DRAFT,
            WorkflowStatus.READY_FOR_REVIEW,
            WorkflowStatus.USER_CONFIRMED,
            WorkflowStatus.SUBMITTED,
            WorkflowStatus.TRACKING,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
        ]

        for status in statuses:
            case = CitizenCase(
                case_id=f"case_{status.value}",
                user_id="user_123",
                input_text="Test",
                workflow_status=status,
            )
            assert case.workflow_status == status

    def test_automation_mode_values(self):
        """Test automation mode enum values."""
        modes = [
            AutomationMode.NONE,
            AutomationMode.API,
            AutomationMode.BROWSER,
            AutomationMode.GUIDED,
            AutomationMode.MANUAL,
        ]

        for mode in modes:
            case = CitizenCase(
                case_id=f"case_{mode.value}",
                user_id="user_123",
                input_text="Test",
                automation_mode=mode,
            )
            assert case.automation_mode == mode


class TestCitizenCaseData:
    """Test CitizenCase data handling."""

    def test_profile_data(self):
        """Test profile data storage."""
        profile_data = {
            "age": 25,
            "occupation": "student",
            "annual_income": 300000,
            "social_category": "OBC",
        }

        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            profile_data=profile_data,
        )

        assert case.profile_data == profile_data
        assert case.profile_data["age"] == 25
        assert case.profile_data["occupation"] == "student"

    def test_extracted_facts(self):
        """Test extracted facts storage."""
        facts = {
            "location": "Chennai, Tamil Nadu",
            "authority": "Chennai Corporation",
            "issue_type": "road_maintenance",
            "duration": "2 years",
        }

        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            extracted_facts=facts,
        )

        assert case.extracted_facts == facts
        assert case.extracted_facts["location"] == "Chennai, Tamil Nadu"

    def test_documents_list(self):
        """Test documents list storage."""
        documents = [
            {"document_id": "doc_001", "type": "photo", "description": "Road condition"},
            {"document_id": "doc_002", "type": "pdf", "description": "Previous complaint"},
        ]

        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            documents=documents,
        )

        assert len(case.documents) == 2
        assert case.documents[0]["document_id"] == "doc_001"
        assert case.documents[1]["type"] == "pdf"

    def test_metadata_storage(self):
        """Test metadata storage."""
        metadata = {
            "source": "mobile_app",
            "language": "tamil",
            "session_id": "sess_123",
        }

        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            metadata=metadata,
        )

        assert case.metadata == metadata
        assert case.metadata["source"] == "mobile_app"


class TestCitizenCaseSubmission:
    """Test submission-related fields."""

    def test_submission_fields(self):
        """Test submission data storage."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            submission_reference_id="REF123456",
            submitted_to_authority="Chennai Corporation",
            submitted_to_portal="CPGRAMS",
        )

        assert case.submission_reference_id == "REF123456"
        assert case.submitted_to_authority == "Chennai Corporation"
        assert case.submitted_to_portal == "CPGRAMS"
        assert case.submitted_at is None  # Not yet submitted

    def test_submission_timestamp(self):
        """Test submission timestamp."""
        submitted_time = datetime.utcnow()

        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            submission_reference_id="REF123456",
            submitted_at=submitted_time,
        )

        assert case.submitted_at == submitted_time


class TestCitizenCaseValidation:
    """Test case validation and constraints."""

    def test_required_fields(self):
        """Test that required fields must be provided."""
        # Should not raise error
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test problem",
        )
        assert case.case_id is not None

    def test_intent_confidence_range(self):
        """Test intent confidence is between 0 and 1."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            intent_confidence=0.85,
        )

        assert 0.0 <= case.intent_confidence <= 1.0

    def test_timestamps_auto_populate(self):
        """Test that timestamps are automatically populated."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
        )

        assert case.created_at is not None
        assert case.updated_at is not None
        assert isinstance(case.created_at, datetime)
        assert isinstance(case.updated_at, datetime)

    def test_default_values(self):
        """Test default values for optional fields."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
        )

        assert case.intent is None
        assert case.intent_confidence == 0.0
        assert case.profile_data == {}
        assert case.extracted_facts == {}
        assert case.documents == []
        assert case.metadata == {}
        assert case.workflow_status == WorkflowStatus.PENDING
        assert case.automation_mode == AutomationMode.NONE


class TestCitizenCaseJurisdiction:
    """Test jurisdiction-related fields."""

    def test_complete_jurisdiction(self):
        """Test all jurisdiction fields."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            state="Tamil Nadu",
            district="Chennai",
            city="Chennai",
            locality="T Nagar",
        )

        assert case.state == "Tamil Nadu"
        assert case.district == "Chennai"
        assert case.city == "Chennai"
        assert case.locality == "T Nagar"

    def test_authority_fields(self):
        """Test authority resolution fields."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            resolved_authority="Chennai Corporation",
            authority_confidence=0.95,
            authority_verified=True,
        )

        assert case.resolved_authority == "Chennai Corporation"
        assert case.authority_confidence == 0.95
        assert case.authority_verified is True


class TestCitizenCaseAutomation:
    """Test automation-related fields."""

    def test_automation_state(self):
        """Test automation state tracking."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            automation_mode=AutomationMode.BROWSER,
            automation_state="filling_form",
            automation_session_id="auto_sess_001",
        )

        assert case.automation_mode == AutomationMode.BROWSER
        assert case.automation_state == "filling_form"
        assert case.automation_session_id == "auto_sess_001"

    def test_blocked_automation(self):
        """Test automation blocking reason."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            automation_mode=AutomationMode.BROWSER,
            automation_blocked_reason="Waiting for OTP",
        )

        assert case.automation_blocked_reason == "Waiting for OTP"


class TestCitizenCaseConsent:
    """Test consent-related fields."""

    def test_consent_flags(self):
        """Test consent flags."""
        case = CitizenCase(
            case_id="case_001",
            user_id="user_123",
            input_text="Test",
            consent_data_sharing=True,
            consent_document_access=True,
            consent_automation=True,
            consent_final_submission=False,
        )

        assert case.consent_data_sharing is True
        assert case.consent_document_access is True
        assert case.consent_automation is True
        assert case.consent_final_submission is False
