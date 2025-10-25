"""
Pytest configuration for test suite.
Defines fixtures, markers, and test configuration.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires network/APIs)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (complete workflows)"
    )


@pytest.fixture(scope="session")
def groq_api_available():
    """Check if Groq API is available."""
    import os
    return bool(os.getenv("GROQ_API_KEY"))


@pytest.fixture
def mock_llm_client():
    """Provide a mock LLM client for unit tests."""
    from unittest.mock import Mock
    from core.interfaces import ILLMClient
    
    mock = Mock(spec=ILLMClient)
    mock.chat.return_value = "Mock response"
    return mock


@pytest.fixture
def mock_library_client():
    """Provide a mock library client for unit tests."""
    from unittest.mock import Mock
    from core.interfaces import ILibraryClient
    
    mock = Mock(spec=ILibraryClient)
    mock.search.return_value = {
        "docs": [],
        "info": {"total": 0}
    }
    return mock


@pytest.fixture
def sample_search_result():
    """Provide sample search result for testing."""
    return {
        "docs": [
            {
                "pnx": {
                    "display": {
                        "title": ["Sample Article Title"],
                        "creator": ["John Doe"],
                        "type": ["article"],
                        "source": ["Sample Journal"],
                        "creationdate": ["2023"]
                    },
                    "addata": {
                        "pub": ["Publisher"],
                        "issn": ["1234-5678"],
                        "doi": ["10.1234/sample"]
                    },
                    "control": {
                        "recordid": ["TN_sample"]
                    }
                },
                "context": "L"
            }
        ],
        "info": {"total": 1}
    }
