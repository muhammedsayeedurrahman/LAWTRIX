"""Database configuration and session management.

PostgreSQL with SQLAlchemy async engine for production persistence.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import get_settings

settings = get_settings()

# Database URL from environment
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/lawtrix"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG if hasattr(settings, "DEBUG") else False,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions.

    Usage in FastAPI:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions (non-FastAPI usage).

    Usage:
        async with get_db_context() as db:
            result = await db.execute(select(Item))
            items = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - create all tables.

    Call this on application startup.
    """
    from backend.db.models import Base  # Import here to avoid circular imports

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all tables (use with caution - testing only)."""
    from backend.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_connection() -> bool:
    """Check if database connection is working."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
