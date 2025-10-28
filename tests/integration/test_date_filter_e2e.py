import pytest
from core.services.search_service import perform_library_search


@pytest.mark.integration
def test_e2e_date_filter_reduces_results():
    """End-to-end via SearchService: filtered results should be <= unfiltered."""
    unfiltered = perform_library_search("quantum computing", limit=10)
    unfiltered_total = unfiltered.get("info", {}).get("total", 0) or len(unfiltered.get("docs", []))

    # Narrow historical range
    filtered = perform_library_search("quantum computing", limit=10, date_from=2000, date_to=2005)
    filtered_total = filtered.get("info", {}).get("total", 0) or len(filtered.get("docs", []))

    assert filtered_total <= unfiltered_total
