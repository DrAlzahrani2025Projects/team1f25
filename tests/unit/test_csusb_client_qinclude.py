from urllib.parse import urlencode

import types

from core.clients.csusb_library_client import CSUSBLibraryClient, S


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
        # Build a query string similar to requests
        query = urlencode(params or {})
        full = f"{url}?{query}"
        self.last_url = full
        return DummyResponse(full, data={"docs": [{"pnx": {"display": {}}}], "info": {"total": 1}})


def test_qinclude_contains_peer_and_rtype(monkeypatch):
    dummy = DummySession()
    # Patch the module-level session used by the client
    monkeypatch.setattr('core.clients.csusb_library_client.S', dummy)

    client = CSUSBLibraryClient()
    # Call search with both peer_reviewed_only and resource_type
    res = client.search(query="test", limit=5, resource_type="article", peer_reviewed_only=True)

    assert res and res.get("docs"), "Expected docs returned"
    # Parse query params to get qInclude value decoded
    from urllib.parse import urlparse, parse_qs, unquote
    qs = urlparse(dummy.last_url).query
    params = parse_qs(qs)
    qinclude = unquote(params.get('qInclude', [''])[0])
    assert "facet_tlevel,exact,peer_reviewed" in qinclude
    assert "facet_rtype,exact,articles" in qinclude


def test_qinclude_absent_when_not_requested(monkeypatch):
    dummy = DummySession()
    monkeypatch.setattr('core.clients.csusb_library_client.S', dummy)

    client = CSUSBLibraryClient()
    res = client.search(query="test", limit=5, resource_type="article", peer_reviewed_only=False)

    assert res and res.get("docs")
    # Parse qInclude to check tokens
    from urllib.parse import urlparse, parse_qs, unquote
    qs = urlparse(dummy.last_url).query
    params = parse_qs(qs)
    qinclude = unquote(params.get('qInclude', [''])[0])
    assert "facet_rtype,exact,articles" in qinclude
    assert "peer_reviewed" not in qinclude
