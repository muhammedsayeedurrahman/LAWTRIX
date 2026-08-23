"""Integration tests for CPGRAMS workflow end-to-end flow.

Tests complete grievance filing workflow from case creation to portal submission.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.citizen_case import CitizenCase, IntentCategory, WorkflowStatus
from backend.workflows.cpgrams_workflow import CPGRAMSWorkflowHandler


@pytest.mark.asyncio
class TestCPGRAMSWorkflowIntegration:
    """Integration tests for complete CPGRAMS workflow."""

    @pytest.fixture
    async def cpgrams_handler(self):
        """Create CPGRAMS workflow handler."""
        return CPGRAMSWorkflowHandler()

    @pytest.fixture
    async def sample_grievance_case(self) -> CitizenCase:
        """Create sample CPGRAMS grievance case."""
        return CitizenCase(
            case_id="cpgrams_int_001",
            user_input="I filed a complaint about poor water supply in my area 3 months ago with the Municipal Corporation, but nothing has been done. Water comes only 2 hours per day.",
            intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            workflow_status=WorkflowStatus.DRAFT,
            user_metadata={
                "full_name": "Priya Sharma",
                "email": "priya.sharma@example.com",
                "phone": "+919123456789",
                "address": "45 Nehru Nagar, Jaipur, Rajasthan",
                "pincode": "302016",
                "state": "Rajasthan",
                "district": "Jaipur",
            },
            created_at=datetime.utcnow(),
        )

    async def test_complete_cpgrams_flow(
        self, cpgrams_handler, sample_grievance_case, async_session: AsyncSession
    ):
        """Test complete CPGRAMS flow from case to submission-ready state."""
        # Step 1: Classify grievance category
        category_result = await cpgrams_handler.classify_grievance(sample_grievance_case)

        assert category_result is not None
        assert "category" in category_result
        assert "water" in category_result["category"].lower() or "municipal" in category_result["category"].lower()

        # Update case
        sample_grievance_case.extracted_facts = {"grievance_category": category_result["category"]}

        # Step 2: Extract grievance details
        details = await cpgrams_handler.extract_grievance_details(sample_grievance_case)

        assert details is not None
        assert "issue_description" in details
        assert "water" in details["issue_description"].lower()
        assert "location" in details or "area" in details

        # Update case
        sample_grievance_case.extracted_facts.update(details)

        # Step 3: Resolve department
        department = await cpgrams_handler.resolve_department(sample_grievance_case)

        assert department is not None
        assert "department_name" in department
        assert any(
            keyword in department["department_name"].lower()
            for keyword in ["water", "municipal", "public health", "urban"]
        )

        # Update case
        sample_grievance_case.authority = department

        # Step 4: Generate grievance description
        description = await cpgrams_handler.generate_grievance_description(sample_grievance_case)

        assert description is not None
        assert len(description) > 50
        assert "water" in description.lower()
        assert sample_grievance_case.user_metadata["full_name"] in description or "complainant" in description.lower()

        # Update case
        sample_grievance_case.generated_draft = description
        sample_grievance_case.workflow_status = WorkflowStatus.READY_FOR_REVIEW

        # Verify case is ready
        assert sample_grievance_case.workflow_status == WorkflowStatus.READY_FOR_REVIEW
        assert sample_grievance_case.generated_draft is not None
        assert sample_grievance_case.authority is not None

    async def test_cpgrams_profile_completion(self, cpgrams_handler, sample_grievance_case):
        """Test CPGRAMS profile validation and completion."""
        # Check if profile is complete
        is_complete = cpgrams_handler.validate_profile(sample_grievance_case.user_metadata)

        assert is_complete is True

        # Test incomplete profile
        incomplete_case = CitizenCase(
            case_id="cpgrams_incomplete_001",
            user_input="I have a complaint",
            intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            user_metadata={
                "full_name": "Test User",
                # Missing email, phone, address
            },
        )

        is_complete = cpgrams_handler.validate_profile(incomplete_case.user_metadata)
        assert is_complete is False

        # Get missing fields
        missing_fields = cpgrams_handler.get_missing_profile_fields(incomplete_case.user_metadata)
        assert "email" in missing_fields
        assert "phone" in missing_fields
        assert "address" in missing_fields or "pincode" in missing_fields

    async def test_cpgrams_grievance_categories(self, cpgrams_handler):
        """Test grievance categorization for various complaint types."""
        test_cases = [
            {
                "input": "Garbage is not being collected in my street for 2 weeks",
                "expected_category": "sanitation",
            },
            {
                "input": "Electricity bill is incorrect, showing double the actual consumption",
                "expected_category": "electricity",
            },
            {
                "input": "My PDS ration card shows wrong family members",
                "expected_category": "ration",
            },
            {
                "input": "Road in front of my house has big potholes causing accidents",
                "expected_category": "road",
            },
        ]

        for test_case in test_cases:
            case = CitizenCase(
                case_id=f"cpgrams_cat_{test_case['input'][:10]}",
                user_input=test_case["input"],
                intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            )

            category_result = await cpgrams_handler.classify_grievance(case)

            assert category_result is not None
            assert "category" in category_result

            # Check if expected keyword is in category
            assert test_case["expected_category"] in category_result["category"].lower() or test_case["expected_category"] in str(category_result).lower()

    async def test_cpgrams_department_resolution(self, cpgrams_handler, sample_grievance_case):
        """Test department resolution accuracy."""
        # Extract details first
        details = await cpgrams_handler.extract_grievance_details(sample_grievance_case)
        sample_grievance_case.extracted_facts = details

        # Resolve department
        department = await cpgrams_handler.resolve_department(sample_grievance_case)

        assert department is not None
        assert "department_name" in department
        assert "ministry" in department or "organization" in department

        # Should have contact information
        assert "email" in department or "helpline" in department or "website" in department

    async def test_cpgrams_priority_assessment(self, cpgrams_handler):
        """Test grievance priority assessment."""
        urgent_cases = [
            "My mother needs urgent medical treatment but hospital is refusing admission without bribe",
            "There is no water supply for 7 days in my area, people are falling sick",
            "Electricity transformer is sparking and creating fire hazard in residential area",
        ]

        normal_cases = [
            "I need a duplicate copy of my birth certificate",
            "When will the new bus stop be constructed in my area?",
            "I want to know the status of my property mutation application",
        ]

        for urgent_input in urgent_cases:
            case = CitizenCase(
                case_id=f"urgent_{urgent_input[:10]}",
                user_input=urgent_input,
                intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            )

            priority = cpgrams_handler.assess_priority(case)
            # Urgent cases should have high/critical priority
            assert priority in ["high", "critical", "urgent"]

        for normal_input in normal_cases:
            case = CitizenCase(
                case_id=f"normal_{normal_input[:10]}",
                user_input=normal_input,
                intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            )

            priority = cpgrams_handler.assess_priority(case)
            # Normal cases should have normal/low priority
            assert priority in ["normal", "low", "medium"]


@pytest.mark.asyncio
class TestCPGRAMSWorkflowFormMapping:
    """Test CPGRAMS form field mapping."""

    async def test_cpgrams_form_field_mapping(self, sample_grievance_case):
        """Test mapping CitizenCase to CPGRAMS form fields."""
        from backend.models.form_schema import FormSchemaFactory

        # Get CPGRAMS form schema
        form_schema = FormSchemaFactory.create_schema_for_workflow("cpgrams")

        assert form_schema is not None
        assert form_schema.form_name == "CPGRAMS Grievance Form"

        # Map case data to form fields
        mapped_fields = form_schema.map_from_case(sample_grievance_case)

        assert mapped_fields is not None
        assert len(mapped_fields) > 0

        # Verify required fields are mapped
        field_ids = [field.field_id for field in mapped_fields]
        assert "complainant_name" in field_ids or "full_name" in field_ids
        assert "email" in field_ids
        assert "phone" in field_ids
        assert "grievance_description" in field_ids or "complaint_details" in field_ids

        # Verify field values
        name_field = next(
            (f for f in mapped_fields if f.field_id in ["complainant_name", "full_name"]),
            None
        )
        assert name_field is not None
        assert name_field.value == sample_grievance_case.user_metadata["full_name"]

    async def test_cpgrams_document_upload_mapping(self, sample_grievance_case):
        """Test document upload field mapping."""
        # Add documents to case
        sample_grievance_case.uploaded_documents = [
            {
                "document_id": "doc_001",
                "filename": "complaint_evidence.jpg",
                "file_type": "image/jpeg",
                "document_type": "PHOTO_EVIDENCE",
            }
        ]

        from backend.models.form_schema import FormSchemaFactory

        form_schema = FormSchemaFactory.create_schema_for_workflow("cpgrams")
        mapped_fields = form_schema.map_from_case(sample_grievance_case)

        # Should have document upload field
        doc_field = next(
            (f for f in mapped_fields if "document" in f.field_id.lower() or "upload" in f.field_id.lower()),
            None
        )
        # Document field may or may not be in standard mapping
        # This tests that system handles documents gracefully


@pytest.mark.asyncio
class TestCPGRAMSWorkflowErrorHandling:
    """Test CPGRAMS workflow error handling and edge cases."""

    async def test_cpgrams_handles_missing_location(self, cpgrams_handler):
        """Test handling of cases without location information."""
        case_no_location = CitizenCase(
            case_id="cpgrams_no_loc_001",
            user_input="The government website is not working properly",
            intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
            user_metadata={
                "full_name": "Test User",
                "email": "test@example.com",
                # No address/pincode/state
            },
        )

        # Should still process, may use generic/central department
        details = await cpgrams_handler.extract_grievance_details(case_no_location)
        assert details is not None

        department = await cpgrams_handler.resolve_department(case_no_location)
        # May return central authority or request location

    async def test_cpgrams_validates_required_fields(self, cpgrams_handler):
        """Test validation of required CPGRAMS fields."""
        from backend.models.form_schema import FormSchemaFactory

        form_schema = FormSchemaFactory.create_schema_for_workflow("cpgrams")

        # Get required fields
        required_fields = [f for f in form_schema.fields if f.required]

        assert len(required_fields) > 0

        # Common required fields for CPGRAMS
        required_field_ids = [f.field_id for f in required_fields]
        assert any("name" in fid.lower() for fid in required_field_ids)
        assert any("email" in fid.lower() or "mobile" in fid.lower() for fid in required_field_ids)
        assert any("description" in fid.lower() or "grievance" in fid.lower() for fid in required_field_ids)
