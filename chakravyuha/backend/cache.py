"""Redis caching service for schemes, sessions, and rate limiting.

Provides caching with TTL, rate limiting, and session state management.
"""

from __future__ import annotations

import json
import os
from typing import Any

try:
    from redis import Redis
    from redis.asyncio import Redis as AsyncRedis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None  # type: ignore
    AsyncRedis = None  # type: ignore


class CacheService:
    """Redis-based caching service with graceful degradation."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = REDIS_AVAILABLE and os.getenv("REDIS_ENABLED", "true").lower() == "true"

        if self.enabled:
            try:
                self.client = AsyncRedis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
            except Exception as e:
                print(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
                self.client = None
        else:
            self.client = None

    async def get(self, key: str) -> str | None:
        """Get value from cache."""
        if not self.enabled or not self.client:
            return None

        try:
            return await self.client.get(key)
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None
    ) -> bool:
        """Set value in cache with optional TTL (seconds)."""
        if not self.enabled or not self.client:
            return False

        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled or not self.client:
            return False

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.enabled or not self.client:
            return False

        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    # ── Scheme Caching ───────────────────────────────────────────────────────

    async def get_schemes(self, cache_key: str) -> list[dict] | None:
        """Get cached schemes data."""
        cached = await self.get(f"schemes:{cache_key}")
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None

    async def set_schemes(
        self,
        cache_key: str,
        schemes: list[dict],
        ttl: int = 86400  # 24 hours default
    ) -> bool:
        """Cache schemes data with TTL."""
        return await self.set(
            f"schemes:{cache_key}",
            json.dumps(schemes),
            ttl=ttl
        )

    async def invalidate_schemes(self, cache_key: str | None = None) -> bool:
        """Invalidate scheme cache."""
        if cache_key:
            return await self.delete(f"schemes:{cache_key}")
        else:
            # Invalidate all scheme caches
            if not self.enabled or not self.client:
                return False
            try:
                keys = await self.client.keys("schemes:*")
                if keys:
                    await self.client.delete(*keys)
                return True
            except Exception as e:
                print(f"Redis invalidate error: {e}")
                return False

    # ── Rate Limiting ────────────────────────────────────────────────────────

    async def check_rate_limit(
        self,
        user_id: str,
        limit: int = 100,
        window: int = 3600  # 1 hour
    ) -> tuple[bool, int]:
        """Check if user is within rate limit.

        Returns:
            (allowed: bool, remaining: int)
        """
        if not self.enabled or not self.client:
            return True, limit  # Allow if Redis unavailable

        try:
            key = f"rate_limit:{user_id}"
            current = await self.client.incr(key)

            if current == 1:
                # First request in window, set expiry
                await self.client.expire(key, window)

            remaining = max(0, limit - current)
            allowed = current <= limit

            return allowed, remaining
        except Exception as e:
            print(f"Redis rate limit error: {e}")
            return True, limit  # Fail open

    async def reset_rate_limit(self, user_id: str) -> bool:
        """Reset rate limit for user."""
        return await self.delete(f"rate_limit:{user_id}")

    # ── Session State ────────────────────────────────────────────────────────

    async def get_session(self, session_id: str) -> dict | None:
        """Get session state."""
        cached = await self.get(f"session:{session_id}")
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None

    async def set_session(
        self,
        session_id: str,
        state: dict,
        ttl: int = 1800  # 30 minutes default
    ) -> bool:
        """Set session state with TTL."""
        return await self.set(
            f"session:{session_id}",
            json.dumps(state),
            ttl=ttl
        )

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        return await self.delete(f"session:{session_id}")

    async def extend_session(
        self,
        session_id: str,
        ttl: int = 1800
    ) -> bool:
        """Extend session TTL."""
        if not self.enabled or not self.client:
            return False

        try:
            await self.client.expire(f"session:{session_id}", ttl)
            return True
        except Exception as e:
            print(f"Redis extend session error: {e}")
            return False

    # ── Generic JSON Caching ─────────────────────────────────────────────────

    async def cache_json(
        self,
        key: str,
        data: dict | list,
        ttl: int | None = None
    ) -> bool:
        """Cache any JSON-serializable data."""
        return await self.set(key, json.dumps(data), ttl=ttl)

    async def get_json(self, key: str) -> dict | list | None:
        """Get cached JSON data."""
        cached = await self.get(key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.aclose()


# Singleton instance
_cache_service: CacheService | None = None


def get_cache() -> CacheService:
    """Get singleton cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
