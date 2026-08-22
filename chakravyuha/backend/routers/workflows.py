"""HTTP endpoints for unified workflow system.

Provides REST API for all civic/legal workflows integrated with CitizenCase.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from backend.db.repository import CaseRepository
from backend.models.citizen_case import CitizenCase, IntentCategory
from backend.workflows.base import (
    ActionPreview,
    ExecutionResult,
    PrepareResult,
    TrackingResult,
    ValidationResult,
)
from backend.workflows.consumer import ConsumerWorkflowHandler
from backend.workflows.cpgrams import CPGRAMSWorkflowHandler
from backend.workflows.labour import LabourWorkflowHandler
from backend.workflows.rti import RTIWorkflowHandler
from backend.workflows.tenant import TenantWorkflowHandler


router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


# ── Request/Response Models ──────────────────────────────────────────────


class WorkflowPrepareRequest(BaseModel):
    """Request to prepare a workflow."""
    case_id: str = Field(..., description="Citizen case ID")


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""
    case_id: str = Field(..., description="Citizen case ID")


class WorkflowTrackRequest(BaseModel):
    """Request to track a workflow."""
    case_id: str = Field(..., description="Citizen case ID")


class WorkflowResponse(BaseModel):
    """Generic workflow operation response."""
    success: bool
    message: str | None = None
    data: dict | None = None
    error: str | None = None


# ── Workflow Selection ───────────────────────────────────────────────────


def get_workflow_handler(intent_category: IntentCategory | str):
    """Get appropriate workflow handler for intent category."""
    if isinstance(intent_category, str):
        try:
            intent_category = IntentCategory(intent_category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid intent category: {intent_category}"
            )

    handlers = {
        IntentCategory.INFORMATION_REQUEST: RTIWorkflowHandler(),
        IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE: CPGRAMSWorkflowHandler(),
        IntentCategory.CONSUMER_RIGHTS: ConsumerWorkflowHandler(),
        IntentCategory.TENANT_RIGHTS: TenantWorkflowHandler(),
        IntentCategory.LABOUR_RIGHTS: LabourWorkflowHandler(),
    }

    handler = handlers.get(intent_category)
    if not handler:
        raise HTTPException(
            status_code=400,
            detail=f"No workflow handler for intent: {intent_category}"
        )

    return handler


async def get_case_from_repo(case_id: str) -> CitizenCase:
    """Get citizen case from repository."""
    from backend.database import get_async_session

    async with get_async_session() as session:
        repo = CaseRepository(session)
        case = await repo.get(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
        return case


# ── Unified Workflow Endpoints ──────────────────────────────────────────


@router.post("/prepare")
async def prepare_workflow(
    request: Annotated[WorkflowPrepareRequest, Body()]
) -> PrepareResult:
    """Prepare a workflow: analyze case, identify requirements, generate draft.

    Returns:
        PrepareResult with required/known/missing fields, draft document, authority, etc.
    """
    case = await get_case_from_repo(request.case_id)
    handler = get_workflow_handler(case.intent.category)

    prepare_result = await handler.prepare(case)
    return prepare_result


@router.post("/validate")
async def validate_workflow(
    request: Annotated[WorkflowPrepareRequest, Body()]
) -> ValidationResult:
    """Validate if workflow is ready to execute.

    Returns:
        ValidationResult with ready status, blockers, and warnings.
    """
    case = await get_case_from_repo(request.case_id)
    handler = get_workflow_handler(case.intent.category)

    validation_result = await handler.validate(case)
    return validation_result


@router.post("/preview")
async def preview_workflow_action(
    request: Annotated[WorkflowPrepareRequest, Body()]
) -> ActionPreview:
    """Preview what will happen when workflow is executed.

    Returns:
        ActionPreview with authority, documents, data shared, fees, risks, next steps.
    """
    case = await get_case_from_repo(request.case_id)
    handler = get_workflow_handler(case.intent.category)

    preview = await handler.preview_action(case)
    return preview


@router.post("/execute")
async def execute_workflow(
    request: Annotated[WorkflowExecuteRequest, Body()]
) -> ExecutionResult:
    """Execute the workflow action.

    IMPORTANT: This requires user confirmation. Check requires_confirmation() first.

    Returns:
        ExecutionResult with status, reference_id, next_steps, or error.
    """
    case = await get_case_from_repo(request.case_id)
    handler = get_workflow_handler(case.intent.category)

    # Check if confirmation required
    if handler.requires_confirmation(case):
        if not case.consent.final_submission:
            return ExecutionResult(
                status="pending_user_action",
                message="User confirmation required before execution",
                next_steps=[
                    "User must review and confirm the action",
                    "Set case.consent.final_submission = True",
                    "Then retry execution",
                ],
            )

    execution_result = await handler.execute(case)
    return execution_result


@router.post("/track")
async def track_workflow(
    request: Annotated[WorkflowTrackRequest, Body()]
) -> TrackingResult:
    """Track status of submitted workflow action.

    Returns:
        TrackingResult with current status, last updated, next check time.
    """
    case = await get_case_from_repo(request.case_id)
    handler = get_workflow_handler(case.intent.category)

    tracking_result = await handler.track(case)
    return tracking_result


@router.get("/requires-confirmation/{case_id}")
async def check_requires_confirmation(case_id: str) -> dict:
    """Check if workflow requires explicit user confirmation.

    Returns:
        {"requires_confirmation": bool, "workflow": str}
    """
    case = await get_case_from_repo(case_id)
    handler = get_workflow_handler(case.intent.category)

    return {
        "requires_confirmation": handler.requires_confirmation(case),
        "workflow": handler.workflow_name,
    }


# ── Specific Workflow Endpoints ─────────────────────────────────────────


@router.post("/rti/prepare")
async def prepare_rti(request: Annotated[WorkflowPrepareRequest, Body()]) -> PrepareResult:
    """Prepare RTI application workflow."""
    case = await get_case_from_repo(request.case_id)
    handler = RTIWorkflowHandler()
    return await handler.prepare(case)


@router.post("/cpgrams/prepare")
async def prepare_cpgrams(request: Annotated[WorkflowPrepareRequest, Body()]) -> PrepareResult:
    """Prepare CPGRAMS grievance workflow."""
    case = await get_case_from_repo(request.case_id)
    handler = CPGRAMSWorkflowHandler()
    return await handler.prepare(case)


@router.post("/consumer/prepare")
async def prepare_consumer(request: Annotated[WorkflowPrepareRequest, Body()]) -> PrepareResult:
    """Prepare consumer complaint workflow."""
    case = await get_case_from_repo(request.case_id)
    handler = ConsumerWorkflowHandler()
    return await handler.prepare(case)


@router.post("/tenant/prepare")
async def prepare_tenant(request: Annotated[WorkflowPrepareRequest, Body()]) -> PrepareResult:
    """Prepare tenant dispute workflow."""
    case = await get_case_from_repo(request.case_id)
    handler = TenantWorkflowHandler()
    return await handler.prepare(case)


@router.post("/labour/prepare")
async def prepare_labour(request: Annotated[WorkflowPrepareRequest, Body()]) -> PrepareResult:
    """Prepare labour dispute workflow."""
    case = await get_case_from_repo(request.case_id)
    handler = LabourWorkflowHandler()
    return await handler.prepare(case)


# ── Workflow Discovery ───────────────────────────────────────────────────


@router.get("/available")
async def list_available_workflows() -> dict:
    """List all available workflow types.

    Returns:
        Dict mapping intent categories to workflow names and descriptions.
    """
    return {
        "workflows": [
            {
                "intent": IntentCategory.INFORMATION_REQUEST.value,
                "workflow": "rti",
                "name": "RTI Application",
                "description": "Request government records and information under Right to Information Act",
            },
            {
                "intent": IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE.value,
                "workflow": "cpgrams",
                "name": "CPGRAMS Grievance",
                "description": "File complaints about government services and departments",
            },
            {
                "intent": IntentCategory.CONSUMER_RIGHTS.value,
                "workflow": "consumer",
                "name": "Consumer Complaint",
                "description": "File consumer complaints for defective products, refunds, warranties",
            },
            {
                "intent": IntentCategory.TENANT_RIGHTS.value,
                "workflow": "tenant",
                "name": "Tenant Dispute",
                "description": "Handle tenant-landlord disputes (deposit, eviction, maintenance)",
            },
            {
                "intent": IntentCategory.LABOUR_RIGHTS.value,
                "workflow": "labour",
                "name": "Labour Dispute",
                "description": "Handle employment issues (unpaid wages, termination, PF, ESI)",
            },
        ]
    }


@router.get("/health")
async def workflow_health_check() -> dict:
    """Health check for workflow system.

    Returns:
        Status of all workflow handlers.
    """
    handlers = {
        "rti": RTIWorkflowHandler(),
        "cpgrams": CPGRAMSWorkflowHandler(),
        "consumer": ConsumerWorkflowHandler(),
        "tenant": TenantWorkflowHandler(),
        "labour": LabourWorkflowHandler(),
    }

    return {
        "status": "healthy",
        "workflows": {
            name: {
                "name": handler.workflow_name,
                "available": True,
            }
            for name, handler in handlers.items()
        },
    }
