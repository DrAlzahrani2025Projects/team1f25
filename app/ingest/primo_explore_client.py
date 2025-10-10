# app/ingest/primo_explore_client.py
from __future__ import annotations
import os, time
from typing import Dict, Any, Optional
import requests

# Use the public "pub" endpoint for Primo VE (keyless)
PRIMO_PUBLIC_BASE = os.environ.get(
    "PRIMO_PUBLIC_BASE",
    "https://csu-sb.primo.exlibrisgroup.com/primaws/rest/pub"
)

# CSUSB defaults (override via env if needed)
PRIMO_VID   = os.environ.get("PRIMO_VID",   "01CALS_USB:01CALS_USB")
PRIMO_TAB   = os.environ.get("PRIMO_TAB",   "CSUSB_CSU_Articles")
PRIMO_SCOPE = os.environ.get("PRIMO_SCOPE", "CSUSB_CSU_articles")
PRIMO_INST  = os.environ.get("PRIMO_INST",  "01CALS_USB")

PRIMO_DELAY   = float(os.environ.get("PRIMO_PUBLIC_RATE_DELAY", "0.2"))
PRIMO_TIMEOUT = int(os.environ.get("PRIMO_PUBLIC_TIMEOUT", "20"))

SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/json",
    "User-Agent": "CSUSB-ScholarBot/0.7 (team1f25)",
    "X-Requested-With": "XMLHttpRequest",
})

def explore_search(  # kept name so your imports/UI don't change
    query: str,
    limit: int = 10,
    offset: int = 0,
    vid: Optional[str] = None,
    tab: Optional[str] = None,
    scope: Optional[str] = None,
    inst: Optional[str] = None,
    lang: str = "en",
    sort: str = "rank",
    mode: str = "advanced",
) -> Dict[str, Any]:
    """
    Call the public 'pub/pnxs' endpoint with the flags the Discovery UI uses.
    """
    params = {
        "vid":   vid   or PRIMO_VID,
        "tab":   tab   or PRIMO_TAB,
        "scope": scope or PRIMO_SCOPE,
        "q":     f"any,contains,{query}",
        "inst":  inst  or PRIMO_INST,
        "limit": str(max(1, min(limit, 50))),
        "offset": str(max(0, offset)),

        # UI-ish flags that reduce 400s
        "lang": lang,
        "mode": mode,
        "sort": sort,
        "skipDelivery": "Y",
        "rtaLinks": "true",
        "rapido": "true",

        # benign defaults commonly present in UI requests
        "acTriggered": "false",
        "blendFacetsSeparately": "false",
        "citationTrailFilterByAvailability": "true",
        "disableCache": "false",
        "getMore": "0",
        "isCDSearch": "false",
        "newspapersActive": "true",
        "newspapersSearch": "false",
        "otbRanking": "false",
        "pcAvailability": "false",
        "qExclude": "",
        "qInclude": "",
        "refEntryActive": "false",
        "searchInFulltextUserSelection": "false",
        "showPnx": "true",
    }

    url = f"{PRIMO_PUBLIC_BASE.rstrip('/')}/pnxs"
    time.sleep(PRIMO_DELAY)
    r = SESSION.get(url, params=params, timeout=PRIMO_TIMEOUT)
    if r.status_code >= 400:
        raise requests.HTTPError(
            f"Explore API {r.status_code} on {url}\nParams={params}\nBody={r.text[:1000]}",
            response=r
        )
    return r.json()

def explore_get_record(record_id: str, context: str = "PC", vid: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch a full record from the public endpoint.
    """
    url = f"{PRIMO_PUBLIC_BASE.rstrip('/')}/pnxs/{context}/{record_id}"
    params = {"vid": vid or PRIMO_VID}
    time.sleep(PRIMO_DELAY)
    r = SESSION.get(url, params=params, timeout=PRIMO_TIMEOUT)
    r.raise_for_status()
    return r.json()

def explore_get_record(record_id: str, context: str = "PC", vid: Optional[str] = None,
                       lang: str = "en", inst: Optional[str] = None,
                       tab: Optional[str] = None, scope: Optional[str] = None) -> Dict[str, Any]:
    url = f"{PRIMO_PUBLIC_BASE.rstrip('/')}/pnxs/{context}/{record_id}"
    params = {
        "vid": vid or PRIMO_VID,
        "lang": lang,
    }
    if inst or PRIMO_INST: params["inst"]  = inst  or PRIMO_INST
    if tab  or PRIMO_TAB:  params["tab"]   = tab   or PRIMO_TAB
    if scope or PRIMO_SCOPE: params["scope"] = scope or PRIMO_SCOPE
    time.sleep(PRIMO_DELAY)
    r = SESSION.get(url, params=params, timeout=PRIMO_TIMEOUT)
    r.raise_for_status()
    return r.json()

def fetch_full_with_fallback(record_id: str, context_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Try the hinted context, then Local ('L'), then Primo Central ('PC').
    Returns the JSON with 'pnx' if any succeed; raises last error otherwise.
    """
    order = []
    if context_hint: order.append(context_hint)
    for c in ("L", "PC"):
        if c not in order: order.append(c)

    last_err = None
    for ctx in order:
        try:
            return explore_get_record(record_id, context=ctx)
        except Exception as e:
            last_err = e
            continue
    raise last_err if last_err else RuntimeError(f"Could not fetch PNX for {record_id}")

