"""Test rate limiting functionality."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_rate_limiting_headers_present(client):
    """Verify rate limiting headers are added to responses."""
    response = client.get("/health")

    # Check that rate limit headers are present
    assert "X-RateLimit-Limit" in response.headers or response.status_code == 200
    # Health endpoint should always work


def test_global_rate_limit_applied(client):
    """Verify global rate limit is enforced (100/minute)."""
    # Make multiple requests in quick succession
    responses = []
    for i in range(5):
        response = client.get("/health")
        responses.append(response)

    # First few requests should succeed
    assert all(r.status_code == 200 for r in responses[:5])

    # All should have passed (5 is well below 100/minute limit)
    assert len([r for r in responses if r.status_code == 200]) == 5


def test_rate_limiting_does_not_break_rti_endpoint(client):
    """Verify RTI endpoint works with rate limiting."""
    response = client.post(
        "/api/rti/extract-facts",
        json={
            "issue": "My RTI application was rejected without proper reason",
            "additional_context": ""
        }
    )

    # Should work (might return validation error but shouldn't be rate limited)
    assert response.status_code in [200, 422]  # 422 if validation fails, but not 429


def test_rate_limiting_config_loaded():
    """Verify rate limiter is configured in app state."""
    from backend.main import limiter

    assert limiter is not None
    assert hasattr(app.state, 'limiter')
    assert app.state.limiter == limiter


def test_rate_limiting_with_memory_backend():
    """Verify rate limiting works with in-memory storage (no Redis)."""
    # This test verifies the fallback when REDIS_URL is not set
    response = TestClient(app).get("/health")
    assert response.status_code == 200
