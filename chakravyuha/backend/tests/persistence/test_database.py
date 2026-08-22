"""Unit tests for database persistence layer."""

from __future__ import annotations

import pytest

from chakravyuha.backend.models.citizen_case import CitizenCase, IntentCategory, WorkflowStatus
from chakravyuha.backend.persistence.database import DatabaseManager


@pytest.mark.asyncio
class TestDatabaseManager:
    """Test DatabaseManager operations."""

    async def test_create_case(self, db_manager, sample_case_data):
        """Test creating a new case."""
        case_id = await db_manager.create_case(sample_case_data)

        assert case_id is not None
        assert isinstance(case_id, str)
        assert case_id.startswith("case_")

    async def test_get_case_exists(self, db_manager, sample_citizen_case):
        """Test retrieving an existing case."""
        # Create case first
        case_data = {
            "user_id": sample_citizen_case.user_id,
            "input_text": sample_citizen_case.input_text,
            "intent": sample_citizen_case.intent,
            "workflow_name": sample_citizen_case.workflow_name,
        }
        case_id = await db_manager.create_case(case_data)

        # Retrieve it
        retrieved = await db_manager.get_case(case_id)

        assert retrieved is not None
        assert retrieved.case_id == case_id
        assert retrieved.user_id == sample_citizen_case.user_id
        assert retrieved.input_text == sample_citizen_case.input_text

    async def test_get_case_not_found(self, db_manager):
        """Test retrieving non-existent case returns None."""
        case = await db_manager.get_case("nonexistent_case_id")
        assert case is None

    async def test_update_case(self, db_manager, sample_case_data):
        """Test updating an existing case."""
        # Create case
        case_id = await db_manager.create_case(sample_case_data)

        # Update it
        updates = {
            "workflow_status": WorkflowStatus.READY_FOR_REVIEW,
            "problem_summary": "Updated summary",
        }
        success = await db_manager.update_case(case_id, updates)

        assert success is True

        # Verify updates
        updated_case = await db_manager.get_case(case_id)
        assert updated_case.workflow_status == WorkflowStatus.READY_FOR_REVIEW
        assert updated_case.problem_summary == "Updated summary"

    async def test_update_nonexistent_case(self, db_manager):
        """Test updating non-existent case returns False."""
        success = await db_manager.update_case("nonexistent", {"status": "draft"})
        assert success is False

    async def test_list_user_cases(self, db_manager):
        """Test listing all cases for a user."""
        user_id = "test_user_123"

        # Create multiple cases
        for i in range(3):
            await db_manager.create_case({
                "user_id": user_id,
                "input_text": f"Test problem {i}",
            })

        # List cases
        cases = await db_manager.list_user_cases(user_id)

        assert len(cases) == 3
        assert all(case.user_id == user_id for case in cases)

    async def test_list_user_cases_empty(self, db_manager):
        """Test listing cases for user with no cases."""
        cases = await db_manager.list_user_cases("user_with_no_cases")
        assert cases == []

    async def test_list_user_cases_with_limit(self, db_manager):
        """Test listing cases with limit."""
        user_id = "test_user_456"

        # Create 5 cases
        for i in range(5):
            await db_manager.create_case({
                "user_id": user_id,
                "input_text": f"Test problem {i}",
            })

        # List with limit
        cases = await db_manager.list_user_cases(user_id, limit=3)

        assert len(cases) == 3

    async def test_delete_case(self, db_manager, sample_case_data):
        """Test deleting a case."""
        # Create case
        case_id = await db_manager.create_case(sample_case_data)

        # Delete it
        success = await db_manager.delete_case(case_id)
        assert success is True

        # Verify deletion
        deleted_case = await db_manager.get_case(case_id)
        assert deleted_case is None

    async def test_delete_nonexistent_case(self, db_manager):
        """Test deleting non-existent case returns False."""
        success = await db_manager.delete_case("nonexistent")
        assert success is False

    async def test_search_cases_by_workflow(self, db_manager):
        """Test searching cases by workflow."""
        user_id = "test_user_789"

        # Create cases with different workflows
        await db_manager.create_case({
            "user_id": user_id,
            "input_text": "RTI request",
            "workflow_name": "rti",
        })
        await db_manager.create_case({
            "user_id": user_id,
            "input_text": "CPGRAMS grievance",
            "workflow_name": "cpgrams",
        })
        await db_manager.create_case({
            "user_id": user_id,
            "input_text": "Another RTI",
            "workflow_name": "rti",
        })

        # Search for RTI cases
        rti_cases = await db_manager.search_cases(
            user_id=user_id,
            workflow_name="rti",
        )

        assert len(rti_cases) == 2
        assert all(case.workflow_name == "rti" for case in rti_cases)

    async def test_search_cases_by_status(self, db_manager):
        """Test searching cases by status."""
        user_id = "test_user_101"

        # Create cases with different statuses
        case1_id = await db_manager.create_case({
            "user_id": user_id,
            "input_text": "Draft case",
        })
        case2_id = await db_manager.create_case({
            "user_id": user_id,
            "input_text": "Submitted case",
        })

        # Update statuses
        await db_manager.update_case(case1_id, {"workflow_status": WorkflowStatus.DRAFT})
        await db_manager.update_case(case2_id, {"workflow_status": WorkflowStatus.SUBMITTED})

        # Search for draft cases
        draft_cases = await db_manager.search_cases(
            user_id=user_id,
            workflow_status=WorkflowStatus.DRAFT,
        )

        assert len(draft_cases) == 1
        assert draft_cases[0].workflow_status == WorkflowStatus.DRAFT

    async def test_case_persistence_with_json_fields(self, db_manager):
        """Test that JSON fields persist correctly."""
        case_data = {
            "user_id": "user_123",
            "input_text": "Test",
            "profile_data": {
                "age": 30,
                "occupation": "engineer",
            },
            "extracted_facts": {
                "location": "Chennai",
                "issue": "road_repair",
            },
            "documents": [
                {"id": "doc1", "type": "photo"},
                {"id": "doc2", "type": "pdf"},
            ],
        }

        case_id = await db_manager.create_case(case_data)
        retrieved = await db_manager.get_case(case_id)

        assert retrieved.profile_data == case_data["profile_data"]
        assert retrieved.extracted_facts == case_data["extracted_facts"]
        assert retrieved.documents == case_data["documents"]
