from datetime import datetime

from core.clients.csusb_library_client import CSUSBLibraryClient


class DummyResp:
    def __init__(self, url="http://example"):
        self.status_code = 200
        self._url = url

    def json(self):
        return {"docs": [], "info": {"total": 0}}

    @property
    def url(self):
        return self._url


def test_builds_date_segment_years():
    client = CSUSBLibraryClient()
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured['params'] = params
        return DummyResp(url=f"{url}?q={params.get('q')}")

    client.session.get = fake_get

    client._explore_search(q="quantum", limit=5, offset=0, date_from=2018, date_to=2019)

    q = captured['params']['q']
    assert 'dr_s,exact,20180101' in q
    assert 'dr_e,exact,20191231' in q


def test_padding_and_swap_and_clamp():
    client = CSUSBLibraryClient()
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured['params'] = params
        return DummyResp(url=f"{url}?q={params.get('q')}")

    client.session.get = fake_get

    # date_from numeric short (20201 -> year=2020 month=1), date_to in future -> clamp and pad
    future_year = datetime.utcnow().year + 10
    client._explore_search(q="ai", limit=5, offset=0, date_from=20201, date_to=future_year)

    q = captured['params']['q']
    today = datetime.utcnow().strftime("%Y%m%d")
    # start normalized to 20200101
    assert 'dr_s,exact,20200101' in q
    # end clamped to today
    assert f'dr_e,exact,{today}' in q
