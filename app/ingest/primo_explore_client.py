# app/ingest/primo_explore_client.py
from __future__ import annotations
import os, time
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.ingest.primo_cache import load_cached, save_cached

# Public Primo VE endpoint (keyless)
PRIMO_PUBLIC_BASE = os.getenv(
    "PRIMO_PUBLIC_BASE",
    "https://csu-sb.primo.exlibrisgroup.com/primaws/rest/pub"
)

# CSUSB defaults (override via env if needed)
PRIMO_VID   = os.getenv("PRIMO_VID",   "01CALS_USB:01CALS_USB")
PRIMO_TAB   = os.getenv("PRIMO_TAB",   "CSUSB_CSU_Articles")
PRIMO_SCOPE = os.getenv("PRIMO_SCOPE", "CSUSB_CSU_articles")
PRIMO_INST  = os.getenv("PRIMO_INST",  "01CALS_USB")

PRIMO_DELAY   = float(os.getenv("PRIMO_PUBLIC_RATE_DELAY", "0.2"))
PRIMO_TIMEOUT = int(os.getenv("PRIMO_PUBLIC_TIMEOUT", "20"))

def _build_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.5,  # 0.5, 1, 2, 4… seconds
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({
        "Accept": "application/json",
        "User-Agent": "CSUSB-ScholarBot/1.0 (team1f25)",
        "X-Requested-With": "XMLHttpRequest",
    })
    return s

SESSION = _build_session()

# ---------------------------
# Core low-level search call
# ---------------------------
def explore_search(
    q: str | None = None,
    limit: int = 10,
    offset: int = 0,
    *,
    query: str | None = None,     # <— alias for backward-compat
    vid: str | None = None,
    tab: str | None = None,
    scope: str | None = None,
    inst: str | None = None,
    lang_ui: str = "en",
    sort: str = "rank",
    mode: str = "advanced",
) -> Dict[str, Any]:
    # alias handling
    if (q is None or q == "") and (query is not None):
        q = query
    if not q:
        raise ValueError("explore_search: missing 'q'/'query'")

    params = {
        "vid":   vid   or PRIMO_VID,
        "tab":   tab   or PRIMO_TAB,
        "scope": scope or PRIMO_SCOPE,
        "q":     q,
        "inst":  inst  or PRIMO_INST,
        "limit": str(max(1, min(limit, 50))),
        "offset": str(max(0, offset)),
        "lang": lang_ui,
        "mode": mode,
        "sort": sort,
        "skipDelivery": "Y",
        "rtaLinks": "true",
        "rapido": "true",
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

# ---------------------------
# Per-record PNX (with cache + fallback)
# ---------------------------
def explore_get_record(record_id: str, context: str = "PC", vid: Optional[str] = None,
                       lang: str = "en", inst: Optional[str] = None,
                       tab: Optional[str] = None, scope: Optional[str] = None) -> Dict[str, Any]:
    url = f"{PRIMO_PUBLIC_BASE.rstrip('/')}/pnxs/{context}/{record_id}"
    params = {"vid": vid or PRIMO_VID, "lang": lang}
    if inst or PRIMO_INST:    params["inst"]  = inst  or PRIMO_INST
    if tab  or PRIMO_TAB:     params["tab"]   = tab   or PRIMO_TAB
    if scope or PRIMO_SCOPE:  params["scope"] = scope or PRIMO_SCOPE

    time.sleep(PRIMO_DELAY)
    r = SESSION.get(url, params=params, timeout=PRIMO_TIMEOUT)
    r.raise_for_status()
    try:
        return r.json()
    except Exception as e:
        raise requests.HTTPError(f"Record API JSON decode error on {url}: {e}")

def fetch_full_with_fallback(record_id: str, context_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Try cache or fetch by hinted context, then Local ('L'), then Primo Central ('PC').
    Cache any successful fetch that has PNX.
    """
    order: List[str] = []
    if context_hint: order.append(context_hint)
    for c in ("L", "PC"):
        if c not in order: order.append(c)

    last_err: Optional[Exception] = None
    for ctx in order:
        # 1) cache
        cached = load_cached(record_id, ctx)
        if cached:
            return cached

        # 2) live fetch
        try:
            data = explore_get_record(record_id, context=ctx)
            if data and data.get("pnx"):
                save_cached(record_id, ctx, data)
            return data
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    raise RuntimeError(f"Could not fetch PNX for {record_id} (contexts tried: {order})")

# ---------------------------
# Filters → query builder & orchestrator (unchanged)
# ---------------------------
def build_q(any_query: str, *, lang_code: str|None, peer_reviewed: bool, rtype: str|None) -> str:
    parts = [f"any,contains,{any_query}"]
    if lang_code:
        parts.append(f"lang,exact,{lang_code}")
    if peer_reviewed:
        parts.append("tlevel,exact,peer_reviewed")
    if rtype:
        parts.append(f"rtype,exact,{rtype}")
    return ",AND;".join(parts)

def _year_from_doc(doc: Dict[str,Any]) -> Optional[int]:
    try:
        year = (doc.get("pnx", {}).get("sort", {}).get("creationdate") or [""])[0]
        return int(str(year)[:4])
    except Exception:
        return None

def _postfilter_by_year(docs: List[Dict[str,Any]], year_from: Optional[int], year_to: Optional[int]) -> List[Dict[str,Any]]:
    if not (year_from or year_to):
        return docs
    out: List[Dict[str,Any]] = []
    for d in docs:
        y = _year_from_doc(d)
        if y is None:
            continue
        if year_from and y < year_from:
            continue
        if year_to and y > year_to:
            continue
        out.append(d)
    return out

def search_with_filters(
    *,
    query: str,
    limit: int = 20,
    offset: int = 0,
    lang_code: Optional[str] = None,
    peer_reviewed: bool = False,
    rtypes: Optional[List[str]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort: str = "rank",
) -> Dict[str, Any]:
    rtypes = [rt for rt in (rtypes or []) if rt] or [None]
    seen = set()
    out_docs: List[Dict[str,Any]] = []
    per_call = min(50, max(10, limit))

    for rt in rtypes:
        local_offset = 0
        while len(out_docs) < limit and local_offset < 500:
            q = build_q(query, lang_code=lang_code or None, peer_reviewed=peer_reviewed, rtype=rt)
            resp = explore_search(q, limit=per_call, offset=local_offset, sort=sort)
            docs = resp.get("docs", []) or []
            if not docs:
                break

            docs = _postfilter_by_year(docs, year_from, year_to)
            for d in docs:
                rid = d.get("id") or (d.get("pnx", {}).get("control", {}).get("recordid") or [""])[0]
                if not rid or rid in seen:
                    continue
                seen.add(rid)
                out_docs.append(d)
                if len(out_docs) >= limit:
                    break

            local_offset += len(docs) if docs else per_call
        if len(out_docs) >= limit:
            break

    return {"docs": out_docs, "total": len(out_docs)}
