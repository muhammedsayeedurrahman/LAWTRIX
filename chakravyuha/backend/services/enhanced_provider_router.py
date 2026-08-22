"""Enhanced provider and model router with health monitoring.

Manages LLM provider selection, failover, and health monitoring.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProviderType(str, Enum):
    """LLM provider types."""
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI = "openai"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


class ModelCapability(str, Enum):
    """Model capabilities."""
    CHAT = "chat"
    EMBEDDING = "embedding"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    LONG_CONTEXT = "long_context"


class ProviderHealth(str, Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ModelConfig(BaseModel):
    """Model configuration."""
    model_config = ConfigDict(frozen=True)

    provider: ProviderType
    model_id: str
    model_name: str
    capabilities: list[ModelCapability]

    # Limits
    max_tokens: int = Field(..., description="Maximum context window")
    max_output_tokens: int | None = None

    # Pricing (per 1M tokens)
    input_cost: float = Field(..., description="Cost per 1M input tokens (USD)")
    output_cost: float = Field(..., description="Cost per 1M output tokens (USD)")

    # Performance
    avg_latency_ms: int | None = Field(None, description="Average latency in milliseconds")

    # Availability
    requires_auth: bool = Field(default=True)
    is_local: bool = Field(default=False)


class ProviderStatus(BaseModel):
    """Provider status and health."""
    model_config = ConfigDict(frozen=True)

    provider: ProviderType
    health: ProviderHealth
    available_models: list[str] = Field(default_factory=list)

    # Health metrics
    last_success: datetime | None = None
    last_failure: datetime | None = None
    failure_count: int = Field(default=0)
    success_count: int = Field(default=0)

    # Performance
    avg_latency_ms: float | None = None
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Metadata
    last_checked: datetime = Field(default_factory=datetime.utcnow)


class WorkflowModelRequirement(BaseModel):
    """Model requirements for a workflow."""
    model_config = ConfigDict(frozen=True)

    workflow_name: str
    required_capabilities: list[ModelCapability] = Field(default_factory=list)
    min_context_window: int = Field(default=8000)
    preferred_providers: list[ProviderType] = Field(default_factory=list)
    fallback_providers: list[ProviderType] = Field(default_factory=list)


class EnhancedProviderRouter:
    """Enhanced provider router with health monitoring and failover."""

    # Model configurations
    MODELS = [
        ModelConfig(
            provider=ProviderType.ANTHROPIC,
            model_id="claude-3-5-sonnet-20241022",
            model_name="Claude 3.5 Sonnet",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.VISION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            max_tokens=200000,
            max_output_tokens=8192,
            input_cost=3.0,
            output_cost=15.0,
        ),
        ModelConfig(
            provider=ProviderType.GEMINI,
            model_id="gemini-1.5-pro",
            model_name="Gemini 1.5 Pro",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.VISION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            max_tokens=2000000,
            max_output_tokens=8192,
            input_cost=1.25,
            output_cost=5.0,
        ),
        ModelConfig(
            provider=ProviderType.OLLAMA,
            model_id="llama3.1:8b",
            model_name="Llama 3.1 8B",
            capabilities=[ModelCapability.CHAT],
            max_tokens=128000,
            input_cost=0.0,  # Free (local)
            output_cost=0.0,
            requires_auth=False,
            is_local=True,
        ),
    ]

    # Workflow requirements
    WORKFLOW_REQUIREMENTS = {
        "rti": WorkflowModelRequirement(
            workflow_name="rti",
            required_capabilities=[ModelCapability.CHAT],
            min_context_window=16000,
            preferred_providers=[ProviderType.GEMINI, ProviderType.ANTHROPIC],
            fallback_providers=[ProviderType.OLLAMA],
        ),
        "cpgrams": WorkflowModelRequirement(
            workflow_name="cpgrams",
            required_capabilities=[ModelCapability.CHAT],
            min_context_window=16000,
            preferred_providers=[ProviderType.GEMINI, ProviderType.ANTHROPIC],
            fallback_providers=[ProviderType.OLLAMA],
        ),
        "consumer": WorkflowModelRequirement(
            workflow_name="consumer",
            required_capabilities=[ModelCapability.CHAT],
            min_context_window=8000,
            preferred_providers=[ProviderType.GEMINI],
            fallback_providers=[ProviderType.ANTHROPIC, ProviderType.OLLAMA],
        ),
        "tenant": WorkflowModelRequirement(
            workflow_name="tenant",
            required_capabilities=[ModelCapability.CHAT],
            min_context_window=8000,
            preferred_providers=[ProviderType.GEMINI],
            fallback_providers=[ProviderType.ANTHROPIC, ProviderType.OLLAMA],
        ),
        "labour": WorkflowModelRequirement(
            workflow_name="labour",
            required_capabilities=[ModelCapability.CHAT],
            min_context_window=8000,
            preferred_providers=[ProviderType.GEMINI],
            fallback_providers=[ProviderType.ANTHROPIC, ProviderType.OLLAMA],
        ),
    }

    def __init__(self):
        # Provider health status (in production, use database)
        self._provider_status: dict[ProviderType, ProviderStatus] = {}
        self._initialize_provider_status()

    def _initialize_provider_status(self):
        """Initialize provider health status."""
        for provider in ProviderType:
            self._provider_status[provider] = ProviderStatus(
                provider=provider,
                health=ProviderHealth.UNKNOWN,
            )

    def select_model_for_workflow(
        self,
        workflow_name: str,
        context_size: int | None = None,
    ) -> ModelConfig | None:
        """Select best model for workflow based on requirements and health.

        Args:
            workflow_name: Workflow name
            context_size: Estimated context size needed

        Returns:
            Selected ModelConfig or None if no suitable model
        """
        requirements = self.WORKFLOW_REQUIREMENTS.get(workflow_name)
        if not requirements:
            # Use default requirements
            requirements = WorkflowModelRequirement(
                workflow_name=workflow_name,
                required_capabilities=[ModelCapability.CHAT],
                min_context_window=8000,
                preferred_providers=[ProviderType.GEMINI, ProviderType.ANTHROPIC],
                fallback_providers=[ProviderType.OLLAMA],
            )

        # Filter models by requirements
        suitable_models = self._filter_models_by_requirements(
            requirements,
            context_size,
        )

        if not suitable_models:
            return None

        # Try preferred providers first
        for provider in requirements.preferred_providers:
            provider_status = self._provider_status.get(provider)
            if provider_status and provider_status.health == ProviderHealth.HEALTHY:
                # Find best model from this provider
                provider_models = [m for m in suitable_models if m.provider == provider]
                if provider_models:
                    # Sort by cost (cheapest first)
                    provider_models.sort(key=lambda m: m.input_cost + m.output_cost)
                    return provider_models[0]

        # Try fallback providers
        for provider in requirements.fallback_providers:
            provider_status = self._provider_status.get(provider)
            if provider_status and provider_status.health != ProviderHealth.UNAVAILABLE:
                provider_models = [m for m in suitable_models if m.provider == provider]
                if provider_models:
                    provider_models.sort(key=lambda m: m.input_cost + m.output_cost)
                    return provider_models[0]

        # Return first suitable model as last resort
        return suitable_models[0] if suitable_models else None

    def _filter_models_by_requirements(
        self,
        requirements: WorkflowModelRequirement,
        context_size: int | None,
    ) -> list[ModelConfig]:
        """Filter models by requirements.

        Args:
            requirements: Workflow requirements
            context_size: Needed context size

        Returns:
            List of suitable models
        """
        suitable = []

        for model in self.MODELS:
            # Check capabilities
            if not all(cap in model.capabilities for cap in requirements.required_capabilities):
                continue

            # Check context window
            min_context = context_size or requirements.min_context_window
            if model.max_tokens < min_context:
                continue

            suitable.append(model)

        return suitable

    async def record_success(
        self,
        provider: ProviderType,
        latency_ms: float | None = None,
    ) -> None:
        """Record successful provider call.

        Args:
            provider: Provider type
            latency_ms: Call latency in milliseconds
        """
        status = self._provider_status.get(provider)
        if not status:
            return

        # Update metrics
        updated_status = status.model_copy(
            update={
                "health": ProviderHealth.HEALTHY,
                "last_success": datetime.utcnow(),
                "success_count": status.success_count + 1,
                "failure_count": 0,  # Reset failure count on success
                "last_checked": datetime.utcnow(),
            }
        )

        # Update average latency
        if latency_ms is not None:
            if status.avg_latency_ms is None:
                updated_status = updated_status.model_copy(
                    update={"avg_latency_ms": latency_ms}
                )
            else:
                # Moving average
                new_avg = (status.avg_latency_ms * 0.9) + (latency_ms * 0.1)
                updated_status = updated_status.model_copy(
                    update={"avg_latency_ms": new_avg}
                )

        self._provider_status[provider] = updated_status

    async def record_failure(
        self,
        provider: ProviderType,
        error_message: str | None = None,
    ) -> None:
        """Record provider failure.

        Args:
            provider: Provider type
            error_message: Error message
        """
        status = self._provider_status.get(provider)
        if not status:
            return

        failure_count = status.failure_count + 1

        # Determine health based on failure count
        if failure_count >= 5:
            health = ProviderHealth.UNAVAILABLE
        elif failure_count >= 2:
            health = ProviderHealth.DEGRADED
        else:
            health = status.health

        updated_status = status.model_copy(
            update={
                "health": health,
                "last_failure": datetime.utcnow(),
                "failure_count": failure_count,
                "last_checked": datetime.utcnow(),
            }
        )

        self._provider_status[provider] = updated_status

    def get_provider_health(self) -> dict[str, Any]:
        """Get health status of all providers.

        Returns:
            Provider health summary
        """
        return {
            "providers": {
                provider.value: {
                    "health": status.health.value,
                    "success_count": status.success_count,
                    "failure_count": status.failure_count,
                    "avg_latency_ms": status.avg_latency_ms,
                    "last_success": status.last_success.isoformat() if status.last_success else None,
                    "last_failure": status.last_failure.isoformat() if status.last_failure else None,
                }
                for provider, status in self._provider_status.items()
            },
            "checked_at": datetime.utcnow().isoformat(),
        }

    def get_workflow_recommendations(self) -> dict[str, dict]:
        """Get model recommendations for each workflow.

        Returns:
            Workflow-to-model recommendations
        """
        recommendations = {}

        for workflow_name in self.WORKFLOW_REQUIREMENTS:
            model = self.select_model_for_workflow(workflow_name)
            if model:
                recommendations[workflow_name] = {
                    "provider": model.provider.value,
                    "model_id": model.model_id,
                    "model_name": model.model_name,
                    "input_cost": model.input_cost,
                    "output_cost": model.output_cost,
                }
            else:
                recommendations[workflow_name] = {
                    "provider": None,
                    "error": "No suitable model available",
                }

        return recommendations
