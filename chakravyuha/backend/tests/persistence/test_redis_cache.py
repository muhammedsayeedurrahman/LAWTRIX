"""Unit tests for Redis caching layer."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from chakravyuha.backend.models.citizen_case import CitizenCase
from chakravyuha.backend.persistence.redis_cache import RedisCache


class TestRedisCache:
    """Test RedisCache operations."""

    def test_set_cache(self, redis_cache, mock_redis):
        """Test setting cache value."""
        key = "test_key"
        value = {"data": "test_value"}

        redis_cache.set(key, value, ttl=300)

        # Verify Redis set was called
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == key
        assert json.loads(call_args[0][1]) == value
        assert call_args[1]["ex"] == 300

    def test_get_cache_exists(self, redis_cache, mock_redis):
        """Test getting existing cache value."""
        key = "test_key"
        value = {"data": "test_value"}
        mock_redis.get.return_value = json.dumps(value).encode()

        result = redis_cache.get(key)

        assert result == value
        mock_redis.get.assert_called_once_with(key)

    def test_get_cache_not_exists(self, redis_cache, mock_redis):
        """Test getting non-existent cache value returns None."""
        mock_redis.get.return_value = None

        result = redis_cache.get("nonexistent_key")

        assert result is None

    def test_delete_cache(self, redis_cache, mock_redis):
        """Test deleting cache entry."""
        key = "test_key"

        redis_cache.delete(key)

        mock_redis.delete.assert_called_once_with(key)

    def test_exists_true(self, redis_cache, mock_redis):
        """Test exists returns True for existing key."""
        mock_redis.exists.return_value = 1

        result = redis_cache.exists("existing_key")

        assert result is True

    def test_exists_false(self, redis_cache, mock_redis):
        """Test exists returns False for non-existent key."""
        mock_redis.exists.return_value = 0

        result = redis_cache.exists("nonexistent_key")

        assert result is False

    def test_set_case(self, redis_cache, mock_redis, sample_citizen_case):
        """Test caching a CitizenCase."""
        redis_cache.set_case(sample_citizen_case, ttl=600)

        # Verify Redis set was called
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args

        expected_key = f"case:{sample_citizen_case.case_id}"
        assert call_args[0][0] == expected_key
        assert call_args[1]["ex"] == 600

        # Verify data was serialized
        serialized_data = json.loads(call_args[0][1])
        assert serialized_data["case_id"] == sample_citizen_case.case_id
        assert serialized_data["user_id"] == sample_citizen_case.user_id

    def test_get_case_exists(self, redis_cache, mock_redis, sample_citizen_case):
        """Test retrieving cached case."""
        # Setup mock to return serialized case
        case_dict = sample_citizen_case.model_dump(mode="json")
        mock_redis.get.return_value = json.dumps(case_dict).encode()

        result = redis_cache.get_case(sample_citizen_case.case_id)

        assert result is not None
        assert isinstance(result, CitizenCase)
        assert result.case_id == sample_citizen_case.case_id
        assert result.user_id == sample_citizen_case.user_id

    def test_get_case_not_exists(self, redis_cache, mock_redis):
        """Test retrieving non-cached case returns None."""
        mock_redis.get.return_value = None

        result = redis_cache.get_case("nonexistent_case")

        assert result is None

    def test_delete_case(self, redis_cache, mock_redis):
        """Test deleting cached case."""
        case_id = "case_001"

        redis_cache.delete_case(case_id)

        expected_key = f"case:{case_id}"
        mock_redis.delete.assert_called_once_with(expected_key)

    def test_cache_intent_classification(self, redis_cache, mock_redis):
        """Test caching intent classification result."""
        input_text = "My road needs repair"
        classification = {
            "intent": "government_service_grievance",
            "confidence": 0.92,
        }

        redis_cache.set_intent_classification(input_text, classification, ttl=1800)

        # Verify caching
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args

        # Check the key format
        assert "intent:" in call_args[0][0]
        assert call_args[1]["ex"] == 1800

    def test_get_intent_classification_exists(self, redis_cache, mock_redis):
        """Test retrieving cached intent classification."""
        classification = {
            "intent": "government_service_grievance",
            "confidence": 0.92,
        }
        mock_redis.get.return_value = json.dumps(classification).encode()

        result = redis_cache.get_intent_classification("My road needs repair")

        assert result == classification

    def test_get_intent_classification_not_exists(self, redis_cache, mock_redis):
        """Test retrieving non-cached intent returns None."""
        mock_redis.get.return_value = None

        result = redis_cache.get_intent_classification("Some new text")

        assert result is None

    def test_cache_workflow_state(self, redis_cache, mock_redis):
        """Test caching workflow state."""
        case_id = "case_001"
        workflow_state = {
            "current_step": "collecting_details",
            "completed_steps": ["intent_classification"],
            "next_step": "authority_resolution",
        }

        redis_cache.set_workflow_state(case_id, workflow_state, ttl=900)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args

        expected_key = f"workflow:{case_id}"
        assert call_args[0][0] == expected_key

    def test_flush_pattern(self, redis_cache, mock_redis):
        """Test flushing keys by pattern."""
        pattern = "case:user_123:*"
        mock_redis.keys.return_value = [
            b"case:user_123:001",
            b"case:user_123:002",
            b"case:user_123:003",
        ]

        redis_cache.flush_pattern(pattern)

        # Verify keys were retrieved and deleted
        mock_redis.keys.assert_called_once_with(pattern)
        assert mock_redis.delete.call_count == 3

    def test_ttl_default(self, redis_cache, mock_redis):
        """Test default TTL is applied."""
        redis_cache.set("key", "value")

        call_args = mock_redis.set.call_args
        # Should have TTL parameter
        assert "ex" in call_args[1]

    def test_json_serialization_edge_cases(self, redis_cache, mock_redis):
        """Test JSON serialization with edge cases."""
        # Test with nested objects
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"key": "value"},
            "null": None,
            "bool": True,
        }

        redis_cache.set("complex", complex_data)

        call_args = mock_redis.set.call_args
        serialized = json.loads(call_args[0][1])

        assert serialized == complex_data
