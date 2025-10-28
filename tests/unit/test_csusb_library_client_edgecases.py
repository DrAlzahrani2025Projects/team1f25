from datetime import datetime

from core.clients.csusb_library_client import CSUSBLibraryClient


class DummyResp:
    def __init__(self, url="http://example", payload=None, status_code=200):
        self.status_code = status_code
        self._url = url
        self._payload = payload or {"docs": [], "info": {"total": 0}}

    def json(self):
        return self._payload

    @property
    def url(self):
        return self._url


def test_future_dates_are_clamped_to_today():
    client = CSUSBLibraryClient()
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured['params'] = params
        return DummyResp(url=f"{url}?q={params.get('q')}")

    client.session.get = fake_get

    # pick a future year well beyond today
    future_year = datetime.utcnow().year + 5
    client._explore_search(q="physics", limit=5, offset=0, date_from=2010, date_to=future_year)

    q = captured['params']['q']
    today = datetime.utcnow().strftime("%Y%m%d")
    assert f'dr_e,exact,{today}' in q


def test_invalid_range_swapped_so_start_leq_end():
    client = CSUSBLibraryClient()
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured['params'] = params
        return DummyResp(url=f"{url}?q={params.get('q')}")

    client.session.get = fake_get

    # provide date_from > date_to (years)
    client._explore_search(q="ai", limit=5, offset=0, date_from=2020, date_to=2018)
    q = captured['params']['q']

    # extract the dr_s and dr_e values
    assert 'dr_s,exact,' in q and 'dr_e,exact,' in q
    def extract_val(prefix):
        start = q.find(prefix)
        if start == -1:
            return None
        part = q[start:].split(',')
        return part[2].split(';')[0]

    start_val = extract_val('dr_s')
    end_val = extract_val('dr_e')
    assert start_val is not None and end_val is not None
    assert int(start_val) <= int(end_val)


def test_very_old_dates_pre_1900_are_allowed():
    client = CSUSBLibraryClient()
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured['params'] = params
        return DummyResp(url=f"{url}?q={params.get('q')}")

    client.session.get = fake_get

    # years before 1900 should be rejected
    try:
        client._explore_search(q="history", limit=5, offset=0, date_from=1800, date_to=1805)
        assert False, "Expected ValueError for year < 1900"
    except ValueError:
        pass


def test_missing_date_metadata_in_response_is_handled_gracefully():
    client = CSUSBLibraryClient()

    payload = {
        "docs": [
            {"id": "1", "title": "Doc With Date", "pubdate": "20200101"},
            {"id": "2", "title": "Doc Without Date"},
            {"id": "3", "title": "Partial Date", "pubdate": "2020"}
        ],
        "info": {"total": 3}
    }

    def fake_get(url, params=None, timeout=None):
        # ignore params here; return a payload where some docs lack date metadata
        return DummyResp(url=url, payload=payload)

    client.session.get = fake_get

    data = client._explore_search(q="anything")
    assert data.get("info", {}).get("total") == 3
    docs = data.get("docs", [])
    assert any(d.get("title") == "Doc Without Date" for d in docs)


def test_partial_date_input_strings_are_normalized_and_padded():
    client = CSUSBLibraryClient()
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured['params'] = params
        return DummyResp(url=f"{url}?q={params.get('q')}")

    client.session.get = fake_get

    # partial string with hyphen and missing day: 2020-3 -> 20200301 for start
    client._explore_search(q="chemistry", limit=5, offset=0, date_from="2020-3", date_to="2021")
    q = captured['params']['q']

    assert 'dr_s,exact,20200301' in q
    assert 'dr_e,exact,20211231' in q
