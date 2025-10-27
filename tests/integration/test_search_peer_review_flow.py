from urllib.parse import urlencode

import pytest

from core.services.search_service import perform_library_search


class DummyResponse:
    def __init__(self, url, data=None):
        self.url = url
        self._data = data or {"docs": [], "info": {"total": 0}}
        self.status_code = 200

    def json(self):
        return self._data


class DummySession:
    def __init__(self):
        self.last_url = None

    def get(self, url, params=None, timeout=None):
        query = urlencode(params or {})
        full = f"{url}?{query}"
        self.last_url = full
        return DummyResponse(full, data={"docs": [{"pnx": {"display": {}}}], "info": {"total": 1}})


def test_perform_library_search_peer_review_flag(monkeypatch):
    # Monkeypatch the CSUSB client session used inside perform_library_search
    import core.clients.csusb_library_client as client_mod
    dummy = DummySession()
    monkeypatch.setattr(client_mod, 'S', dummy)

    # Call legacy perform_library_search which creates its own client
    results = perform_library_search(query="machine learning healthcare", limit=3, resource_type="article", peer_reviewed_only=True)

    assert isinstance(results, dict)
    assert results.get('docs')
    # Decode qInclude from the recorded URL and assert tokens present
    from urllib.parse import urlparse, parse_qs, unquote
    qs = urlparse(dummy.last_url).query
    params = parse_qs(qs)
    qinclude = unquote(params.get('qInclude', [''])[0])
    assert 'facet_tlevel,exact,peer_reviewed' in qinclude

    # Now call without peer_reviewed_only
    results2 = perform_library_search(query="machine learning healthcare", limit=3, resource_type="article", peer_reviewed_only=False)
    assert isinstance(results2, dict)
    assert results2.get('docs')
    # peer_reviewed token should not be present in qInclude
    qs = urlparse(dummy.last_url).query
    params = parse_qs(qs)
    qinclude = unquote(params.get('qInclude', [''])[0])
    assert 'peer_reviewed' not in qinclude
