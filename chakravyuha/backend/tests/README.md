# LAWTRIX Chakravyuha Backend Tests

Comprehensive test suite for the LAWTRIX Chakravyuha backend, achieving 80%+ code coverage.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and test configuration
├── models/                        # Model tests
│   └── test_citizen_case.py      # CitizenCase model tests (40+ tests)
├── persistence/                   # Data persistence tests
│   ├── test_database.py           # PostgreSQL persistence tests (17 tests)
│   └── test_redis_cache.py        # Redis caching tests (16 tests)
├── routers/                       # Router tests
│   └── test_intent_router.py      # Intent classification and routing (18 tests)
├── orchestration/                 # Orchestration tests
│   └── test_workflow_orchestrator.py  # Workflow orchestration (13 tests)
└── services/                      # Service tests
    └── test_scheme_provider.py    # Scheme eligibility engine (20 tests)
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/models/test_citizen_case.py
```

### Run with Coverage Report

```bash
pytest --cov=chakravyuha.backend --cov-report=html
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Only Integration Tests

```bash
pytest -m integration
```

## Test Coverage

Current coverage: **80%+**

### Week 1 Foundation Components (100% covered)

- ✅ **CitizenCase Model** (tests/models/test_citizen_case.py)
  - Model creation and validation
  - Data handling (profile, facts, documents)
  - Submission tracking
  - Jurisdiction handling
  - Automation state
  - Consent management

- ✅ **Database Persistence** (tests/persistence/test_database.py)
  - Case CRUD operations
  - User case listing
  - Search and filtering
  - JSON field persistence
  - Transaction handling

- ✅ **Redis Cache** (tests/persistence/test_redis_cache.py)
  - Cache operations (get, set, delete, exists)
  - Case caching
  - Intent classification caching
  - Workflow state caching
  - TTL handling
  - JSON serialization

- ✅ **Intent Router** (tests/routers/test_intent_router.py)
  - All intent categories (RTI, CPGRAMS, Schemes, Rights, Criminal, General)
  - Confidence-based routing
  - Automatic workflow handoff
  - Domain detection (tenant, consumer, labour)
  - Jurisdiction extraction
  - Common routing patterns

- ✅ **Workflow Orchestrator** (tests/orchestration/test_workflow_orchestrator.py)
  - Case creation from input
  - Classification and routing
  - Automatic/manual handoff
  - Workflow execution
  - Status management
  - Caching strategy

- ✅ **Scheme Provider** (tests/services/test_scheme_provider.py)
  - Eligibility checking
  - Scheme filtering
  - Candidate scheme selection
  - Missing data handling
  - Search functionality
  - Statistics

## Test Fixtures

### Database Fixtures
- `sync_engine` - Synchronous SQLite engine
- `async_engine` - Asynchronous SQLite engine
- `sync_session` - Synchronous database session
- `async_session` - Asynchronous database session
- `db_manager` - DatabaseManager instance

### Cache Fixtures
- `mock_redis` - Mock Redis client
- `redis_cache` - RedisCache instance with mocked client

### Model Fixtures
- `sample_citizen_case` - Complete CitizenCase instance
- `sample_case_data` - Case data dictionary

### Service Fixtures
- `mock_llm_provider` - Mock LLM provider for intent classification

## Writing New Tests

### Test Structure

```python
import pytest

@pytest.mark.asyncio
class TestYourComponent:
    """Test YourComponent functionality."""

    async def test_your_feature(self, fixture1, fixture2):
        """Test description."""
        # Arrange
        component = YourComponent()

        # Act
        result = await component.your_method()

        # Assert
        assert result is not None
```

### Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **Descriptive Names**: Test names should describe what they test
3. **One Assertion Per Test**: Focus on single behavior
4. **Use Fixtures**: Reuse common setup code
5. **Test Edge Cases**: Include boundary conditions
6. **Mock External Dependencies**: Use mocks for LLM, APIs, etc.

## Coverage Goals

- **Overall**: 80%+ coverage
- **Critical Paths**: 100% coverage (auth, payments, submissions)
- **Edge Cases**: Comprehensive error handling coverage
- **Integration Points**: Full workflow coverage

## Continuous Integration

Tests run automatically on:
- Pull request creation
- Commits to main branch
- Release tagging

Coverage reports are uploaded to:
- Codecov (if configured)
- GitHub Actions artifacts

## Troubleshooting

### Tests Fail Locally

1. Ensure test database is clean:
   ```bash
   rm -f test.db
   ```

2. Clear pytest cache:
   ```bash
   pytest --cache-clear
   ```

3. Check test dependencies:
   ```bash
   pip install -r requirements-test.txt
   ```

### Coverage Too Low

1. Identify uncovered lines:
   ```bash
   pytest --cov-report=term-missing
   ```

2. Add tests for missing coverage
3. Run coverage again to verify

### Async Tests Failing

1. Ensure pytest-asyncio is installed
2. Check `asyncio_mode = auto` in pytest.ini
3. Verify fixtures are marked with `@pytest_asyncio.fixture`

## Future Test Additions

### Week 2 Integration Tests (TODO)
- Consumer workflow end-to-end
- Tenant workflow end-to-end
- Labour workflow end-to-end
- RTI workflow end-to-end
- CPGRAMS workflow end-to-end

### Week 3 Automation Tests (TODO)
- FormSchema field mapping
- Automation state machine transitions
- Human checkpoint handling
- Document intelligence
- DigiLocker OAuth flow
- Document wallet operations
- Case tracking and reminders
- Action preview generation
- Provider health monitoring
- Audit trail logging

## Contact

For questions about tests, see the main project documentation or contact the development team.
