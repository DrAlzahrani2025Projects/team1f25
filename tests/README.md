# Tests Directory

This directory contains all test scripts for the Scholar AI Assistant.

## Test Files

### Parameter Extraction Tests
- `test_params.py` - Test parameter extraction from user queries
- `test_journal_vs_article.py` - Test distinction between "journals" and "journal articles"

### Search Functionality Tests
- `test_search.py` - Basic library search functionality
- `test_api_filter.py` - Test API-level resource type filtering
- `test_filtering.py` - Test client-side filtering
- `test_journal.py` - Test journal-specific searches
- `check_types.py` - Check available resource types in results

### End-to-End Tests
- `test_e2e.py` - Complete end-to-end flow test
- `test_user_query.py` - Test specific user queries
- `test_comprehensive.py` - Comprehensive test of all scenarios

### Error Handling Tests
- `test_no_results.py` - Test handling of queries with no results
- `test_suggestions.py` - Test AI-generated search suggestions
- `test_conversation_flow.py` - Test complete conversation flow with error handling

## Running Tests

### Run a specific test:
```bash
python tests/test_search.py
```

### Run all tests:
```bash
# PowerShell
Get-ChildItem tests\test_*.py | ForEach-Object { python $_.FullName }

# Bash
for file in tests/test_*.py; do python "$file"; done
```

## Test Categories

### Unit Tests
- Individual function/module testing
- Examples: `test_params.py`, `test_filtering.py`

### Integration Tests
- Testing module interactions
- Examples: `test_e2e.py`, `test_user_query.py`

### Validation Tests
- Verify API responses and data structures
- Examples: `check_types.py`, `test_api_filter.py`

## Requirements

All tests require:
- Active internet connection (for API calls)
- Valid `GROQ_API_KEY` environment variable
- All dependencies from `requirements.txt` installed

## Notes

- Tests make actual API calls to CSUSB library and Groq
- Some tests may take a few seconds due to API latency
- Test results may vary based on library database content
