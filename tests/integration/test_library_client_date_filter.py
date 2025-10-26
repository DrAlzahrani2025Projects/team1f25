import pytest
from core.clients.csusb_library_client import CSUSBLibraryClient
from core.services.result_formatter import ResultFormatter


@pytest.mark.integration
def test_date_filter_reduces_or_equals_unfiltered_results():
    """Compare unfiltered vs filtered counts to ensure date filter restricts results."""
    client = CSUSBLibraryClient()

    # Run an unfiltered search
    unfiltered = client.search("machine learning", limit=10)
    unfiltered_total = unfiltered.get("info", {}).get("total", 0) or len(unfiltered.get("docs", []))

    # Run a filtered search for a narrow historic range
    filtered = client.search("machine learning", limit=10, date_from=2010, date_to=2012)
    filtered_total = filtered.get("info", {}).get("total", 0) or len(filtered.get("docs", []))

    # Filtered result set should be less than or equal to unfiltered
    assert filtered_total <= unfiltered_total


@pytest.mark.integration
def test_date_filter_returns_docs_within_range():
    """Ensure returned documents (when available) have dates within the requested range."""
    client = CSUSBLibraryClient()

    results = client.search("climate change", limit=20, date_from=2015, date_to=2016)
    docs = results.get("docs", [])

    # If there are no docs, the API may legitimately return none for the range
    if not docs:
        pytest.skip("No results returned for this date range; cannot verify date filtering")

    # Check that at least one document has a parsable year within the range
    ok_found = False
    for doc in docs:
        parsed = ResultFormatter.parse_document(doc)
        year = parsed.get("date")
        if year and year != "N/A":
            try:
                y = int(year)
                if 2015 <= y <= 2016:
                    ok_found = True
                    break
            except ValueError:
                continue

    assert ok_found, "No documents with creation year in the requested range were found"
