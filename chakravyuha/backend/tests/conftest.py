"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from chakravyuha.backend.models.base import Base
from chakravyuha.backend.models.citizen_case import CitizenCase, IntentCategory
from chakravyuha.backend.persistence.database import DatabaseManager
from chakravyuha.backend.persistence.redis_cache import RedisCache


# Test database URLs
TEST_SYNC_DATABASE_URL = "sqlite:///./test.db"
TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def sync_engine():
    """Create synchronous test database engine."""
    engine = create_engine(TEST_SYNC_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create asynchronous test database engine."""
    engine = create_async_engine(TEST_ASYNC_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
def sync_session(sync_engine) -> Generator[Session, None, None]:
    """Create synchronous test database session."""
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create asynchronous test database session."""
    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def db_manager(async_engine) -> DatabaseManager:
    """Create test database manager."""
    manager = DatabaseManager(database_url=TEST_ASYNC_DATABASE_URL)
    manager._engine = async_engine
    return manager


@pytest.fixture(scope="function")
def mock_redis() -> MagicMock:
    """Create mock Redis client."""
    mock = MagicMock(spec=Redis)
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = 0
    mock.keys.return_value = []
    return mock


@pytest.fixture(scope="function")
def redis_cache(mock_redis) -> RedisCache:
    """Create test Redis cache with mocked client."""
    cache = RedisCache(host="localhost", port=6379, db=0)
    cache._client = mock_redis
    return cache


@pytest.fixture(scope="function")
def sample_citizen_case() -> CitizenCase:
    """Create sample CitizenCase for testing."""
    return CitizenCase(
        case_id="test_case_001",
        user_id="user_123",
        input_text="My road has not been repaired for 2 years.",
        intent=IntentCategory.GOVERNMENT_SERVICE_GRIEVANCE,
        intent_confidence=0.92,
        problem_summary="Road repair grievance",
        state="Tamil Nadu",
        district="Chennai",
        workflow_name="cpgrams",
        workflow_status="draft",
    )


@pytest.fixture(scope="function")
def sample_case_data() -> dict:
    """Create sample case data for testing."""
    return {
        "user_id": "user_456",
        "input_text": "I need records of road maintenance spending.",
        "intent": "information_request",
        "intent_confidence": 0.88,
        "problem_summary": "RTI request for road maintenance records",
        "state": "Karnataka",
        "district": "Bangalore",
        "workflow_name": "rti",
        "workflow_status": "pending",
    }


@pytest_asyncio.fixture(scope="function")
async def mock_llm_provider():
    """Create mock LLM provider."""
    provider = AsyncMock()
    provider.classify_intent = AsyncMock(
        return_value={
            "intent": "government_service_grievance",
            "confidence": 0.90,
            "reasoning": "User is complaining about government service",
        }
    )
    provider.extract_facts = AsyncMock(
        return_value={
            "state": "Tamil Nadu",
            "district": "Chennai",
            "problem_type": "road_repair",
        }
    )
    return provider
