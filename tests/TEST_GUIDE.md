# Test Guide

This guide provides comprehensive information about testing the CSUSB Library AI Assistant project.

## Table of Contents
- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Fixtures](#fixtures)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The test suite uses **pytest** as the testing framework and is organized into three main categories:
- **Unit Tests**: Fast, isolated tests with no external dependencies
- **Integration Tests**: Tests that interact with external APIs and services
- **End-to-End Tests**: Complete workflow tests that verify the entire system

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                      # Pytest configuration and fixtures
├── pytest.ini                       # Pytest settings (in root directory)
├── TEST_GUIDE.md                    # This file
│
├── unit/                            # Unit tests
│   ├── __init__.py
│   ├── test_conversation_analyzer.py
│   ├── test_prompts.py
│   ├── test_result_formatter.py
│   └── test_suggestion_service.py
│
├── integration/                     # Integration tests
│   ├── __init__.py
│   ├── test_e2e_workflow.py
│   ├── test_groq_client.py
│   ├── test_library_client.py
│   └── test_search_service.py
│
└── [test files]                     # Functional/scenario tests
    ├── test_api_filter.py
    ├── test_comprehensive.py
    ├── test_conversation_flow.py
    ├── test_display_with_links.py
    ├── test_e2e.py
    ├── test_filtering.py
    ├── test_journal.py
    ├── test_journal_vs_article.py
    ├── test_link_contexts.py
    ├── test_no_results.py
    ├── test_params.py
    ├── test_search.py
    ├── test_strict_scholarly.py
    ├── test_suggestions.py
    └── test_user_query.py
```

## Running Tests

### Prerequisites

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```

2. **Set Environment Variables** (for integration tests):
   ```bash
   # Windows PowerShell
   $env:GROQ_API_KEY="your-groq-api-key"
   
   # Linux/Mac
   export GROQ_API_KEY="your-groq-api-key"
   ```

### Running All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=core --cov-report=html --cov-report=term
```

### Running Specific Test Categories

```bash
# Run only unit tests (fast, no external dependencies)
pytest -m unit

# Run only integration tests (requires API keys)
pytest -m integration

# Run only end-to-end tests
pytest -m e2e

# Exclude integration tests (useful for CI without API keys)
pytest -m "not integration"
```

### Running Specific Test Files

```bash
# Run a specific test file
pytest tests/test_search.py

# Run a specific test function
pytest tests/test_search.py::test_basic_search

# Run tests in a directory
pytest tests/unit/

# Run tests matching a pattern
pytest -k "search"
pytest -k "journal or article"
```

### Using Python Scripts

```bash
# Using the custom test runner
python run_pytest.py

# Using the alternative test runner
python run_tests.py
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

**Purpose**: Test individual components in isolation without external dependencies.

**Characteristics**:
- Fast execution (< 1 second per test)
- Use mocks for external dependencies
- No network calls
- Deterministic results

**Examples**:
- `tests/unit/test_conversation_analyzer.py` - Tests conversation analysis logic
- `tests/unit/test_result_formatter.py` - Tests result formatting functions
- `tests/unit/test_suggestion_service.py` - Tests suggestion generation
- `tests/unit/test_prompts.py` - Tests prompt templates

**Running**:
```bash
pytest -m unit
```

### Integration Tests (`@pytest.mark.integration`)

**Purpose**: Test interaction with external services and APIs.

**Characteristics**:
- Requires network access
- Needs API keys (GROQ_API_KEY)
- Slower execution (1-10 seconds per test)
- May have rate limits

**Examples**:
- `tests/integration/test_groq_client.py` - Tests Groq API integration
- `tests/integration/test_library_client.py` - Tests CSUSB Library API
- `tests/integration/test_search_service.py` - Tests search service with real APIs

**Running**:
```bash
pytest -m integration
```

### End-to-End Tests (`@pytest.mark.e2e`)

**Purpose**: Test complete user workflows from start to finish.

**Characteristics**:
- Tests entire system
- Multiple components working together
- Slowest execution
- Most realistic scenarios

**Examples**:
- `tests/test_e2e.py` - Complete search workflows
- `tests/integration/test_e2e_workflow.py` - Full conversation flows

**Running**:
```bash
pytest -m e2e
```

### Functional Tests (No marker)

**Purpose**: Test specific features and scenarios.

**Examples**:
- `test_api_filter.py` - API filtering functionality
- `test_journal.py` - Journal-specific searches
- `test_journal_vs_article.py` - Differentiation between journals and articles
- `test_no_results.py` - Handling empty search results
- `test_conversation_flow.py` - Multi-turn conversation logic
- `test_filtering.py` - Result filtering logic
- `test_suggestions.py` - Suggestion generation

## Writing Tests

### Basic Test Structure

```python
import pytest
from core.services.search_service import SearchService

@pytest.mark.unit
def test_basic_functionality(mock_library_client):
    """Test description goes here."""
    # Arrange
    service = SearchService(mock_library_client)
    query = "machine learning"
    
    # Act
    result = service.search(query)
    
    # Assert
    assert result is not None
    assert len(result) > 0
```

### Using Fixtures

```python
@pytest.mark.unit
def test_with_fixture(mock_llm_client, sample_search_result):
    """Test using multiple fixtures."""
    # Fixtures are automatically injected
    response = mock_llm_client.chat("test query")
    assert response == "Mock response"
    
    assert sample_search_result["info"]["total"] == 1
```

### Integration Test Example

```python
@pytest.mark.integration
def test_real_api_call(groq_api_available):
    """Test that requires real API."""
    if not groq_api_available:
        pytest.skip("GROQ_API_KEY not set")
    
    from core.clients.groq_client import GroqClient
    client = GroqClient()
    
    response = client.chat("What is machine learning?")
    assert response is not None
    assert len(response) > 0
```

### Parametrized Tests

```python
@pytest.mark.parametrize("query,expected_type", [
    ("I need journals", "journal"),
    ("Find articles", "article"),
    ("Show me books", "book"),
])
def test_resource_type_detection(query, expected_type):
    """Test resource type extraction from various queries."""
    from core.ai_assistant import extract_search_parameters
    params = extract_search_parameters(query)
    assert params["resource_type"] == expected_type
```

## Fixtures

Fixtures are defined in `tests/conftest.py` and are automatically available to all tests.

### Available Fixtures

#### `groq_api_available` (session-scoped)
Checks if the GROQ_API_KEY environment variable is set.

```python
def test_something(groq_api_available):
    if not groq_api_available:
        pytest.skip("API key not available")
```

#### `mock_llm_client`
Provides a mock LLM client for unit tests.

```python
def test_with_mock_llm(mock_llm_client):
    response = mock_llm_client.chat("test")
    assert response == "Mock response"
```

#### `mock_library_client`
Provides a mock library client for unit tests.

```python
def test_with_mock_library(mock_library_client):
    result = mock_library_client.search("test")
    assert result["info"]["total"] == 0
```

#### `sample_search_result`
Provides a sample search result structure for testing.

```python
def test_formatting(sample_search_result):
    docs = sample_search_result["docs"]
    assert len(docs) == 1
    assert docs[0]["pnx"]["display"]["title"][0] == "Sample Article Title"
```

### Creating Custom Fixtures

Add fixtures to `conftest.py`:

```python
@pytest.fixture
def custom_fixture():
    """Your custom fixture description."""
    # Setup
    data = {"key": "value"}
    yield data
    # Teardown (optional)
```

## Best Practices

### 1. Test Naming
- Use descriptive names: `test_search_returns_results_when_query_is_valid`
- Start with `test_`
- Describe what is being tested and the expected outcome

### 2. Test Organization
- One test function per scenario
- Group related tests in the same file
- Use clear section comments

### 3. Assertions
```python
# Good: Specific assertions
assert result["total"] == 5
assert "error" not in response

# Avoid: Generic assertions
assert result
assert response is not None
```

### 4. Mocking
```python
from unittest.mock import Mock, patch

# Mock external dependencies in unit tests
@patch('core.clients.groq_client.GroqClient')
def test_with_mock(mock_groq):
    mock_groq.return_value.chat.return_value = "mocked response"
    # Test code here
```

### 5. Test Data
- Use fixtures for reusable test data
- Keep test data minimal and focused
- Use factories for complex objects

### 6. Error Testing
```python
def test_error_handling():
    """Test that errors are handled correctly."""
    with pytest.raises(ValueError, match="Invalid query"):
        process_query("")
```

### 7. Skipping Tests
```python
@pytest.mark.skip(reason="Feature not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 8), reason="Requires Python 3.8+")
def test_modern_feature():
    pass
```

## Test Markers Reference

| Marker | Purpose | Speed | Dependencies |
|--------|---------|-------|--------------|
| `unit` | Isolated unit tests | Fast | None |
| `integration` | API integration tests | Medium | API keys, network |
| `e2e` | End-to-end workflows | Slow | Full system |
| `slow` | Long-running tests | Slow | Varies |

## Coverage

### Generating Coverage Reports

```bash
# HTML report (opens in browser)
pytest --cov=core --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=core --cov-report=term

# Both
pytest --cov=core --cov-report=html --cov-report=term
```

### Coverage Goals
- **Core modules**: Aim for 80%+ coverage
- **Critical paths**: 100% coverage
- **UI components**: 60%+ coverage

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 2. API Key Not Found
```bash
# Check environment variable
echo $GROQ_API_KEY

# Set it if missing
export GROQ_API_KEY="your-key-here"
```

#### 3. Tests Running Slowly
```bash
# Run only fast unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

#### 4. Flaky Tests
- Integration tests may fail due to network issues
- Use retries for flaky tests:
```python
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_flaky_network_call():
    pass
```

#### 5. Mock Not Working
- Ensure you're patching the right location
- Patch where the object is used, not where it's defined:
```python
# If module A imports function from module B and uses it:
# Patch in module A, not module B
@patch('module_a.function_from_b')
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run unit tests
        run: pytest -m unit
      - name: Run integration tests
        if: ${{ secrets.GROQ_API_KEY }}
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
        run: pytest -m integration
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Mocking in Python](https://docs.python.org/3/library/unittest.mock.html)

## Contributing

When adding new tests:

1. Choose the appropriate category (unit/integration/e2e)
2. Add appropriate markers
3. Update this guide if introducing new patterns
4. Ensure tests are deterministic
5. Add docstrings to test functions
6. Keep tests focused and minimal

## Quick Reference Commands

```bash
# Run all tests
pytest

# Run specific category
pytest -m unit
pytest -m integration
pytest -m e2e

# Run specific file
pytest tests/test_search.py

# Run with coverage
pytest --cov=core --cov-report=term

# Run in verbose mode
pytest -v

# Run tests matching pattern
pytest -k "search"

# Skip integration tests
pytest -m "not integration"

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

---

**Last Updated**: October 2025  
**Maintainer**: CSUSB Library AI Assistant Team
