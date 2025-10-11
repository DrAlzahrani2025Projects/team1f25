# app/ingest/primo_explore_client.py
from __future__ import annotations
import os, time
from typing import Dict, Any, Optional, List, Tuple, Set
import requests
from datetime import datetime

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

SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/json",
    "User-Agent": "CSUSB-ScholarBot/0.9 (team1f25)",
    "X-Requested-With": "XMLHttpRequest",
})

# ---------------------------
# Core low-level search call
# ---------------------------
def explore_search(
    q: str,
    limit: int = 10,
    offset: int = 0,
    *,
    vid: Optional[str] = None,
    tab: Optional[str] = None,
    scope: Optional[str] = None,
    inst: Optional[str] = None,
    lang_ui: str = "en",
    sort: str = "rank",           # 'rank' | 'date'
    mode: str = "advanced",
) -> Dict[str, Any]:
    """
    Low-level call to public 'pub/pnxs'. Expects 'q' fully formed (e.g., "any,contains,ai,AND;lang,exact,eng").
    """
    params = {
        "vid":   vid   or PRIMO_VID,
        "tab":   tab   or PRIMO_TAB,
        "scope": scope or PRIMO_SCOPE,
        "q":     q,
        "inst":  inst  or PRIMO_INST,
        "limit": str(max(1, min(limit, 50))),
        "offset": str(max(0, offset)),

        # UI-ish flags that reduce 400s
        "lang": lang_ui,
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

        # ask for pnx if tenant honors it (harmless if ignored)
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
# Per-record PNX (with fallback)
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
    return r.json()

def fetch_full_with_fallback(record_id: str, context_hint: Optional[str] = None) -> Dict[str, Any]:
    order: List[str] = []
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

# ---------------------------
# Filters → query builder
# ---------------------------
def build_q(any_query: str, *, lang_code: str|None, peer_reviewed: bool, rtype: str|None) -> str:
    """
    Compose the 'q' string that Primo expects.
    We encode filters as additional clauses:
      - language:  lang,exact,<code>   (e.g., eng)
      - peer rev:  tlevel,exact,peer_reviewed
      - rtype:     rtype,exact,<val>   (e.g., articles, dissertations, books)
    """
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
        y = int(str(year)[:4])
        return y
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

# ---------------------------
# High-level filtered search
# ---------------------------
def search_with_filters(
    *,
    query: str,
    limit: int = 20,
    offset: int = 0,
    lang_code: Optional[str] = None,          # e.g., 'eng' or ''
    peer_reviewed: bool = False,
    rtypes: Optional[List[str]] = None,        # e.g., ['articles','dissertations']
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort: str = "rank",                        # 'rank' | 'date'
) -> Dict[str, Any]:
    """
    Orchestrates multi-rtype union and client-side year filtering.
    For multiple resource types, we union results across calls (OR behavior).
    Returns a dict with 'docs' and 'total' (approx).
    """
    rtypes = [rt for rt in (rtypes or []) if rt] or [None]  # None means "no rtype filter"

    # We'll collect unique docs by 'id'
    seen: Set[str] = set()
    out_docs: List[Dict[str,Any]] = []

    # We may overfetch per-rtype to have room for post-filtering by year
    per_call = min(50, max(10, limit))
    cur_offset = offset

    for rt in rtypes:
        # Build q with this rtype (or without)
        q = build_q(query, lang_code=lang_code or None, peer_reviewed=peer_reviewed, rtype=rt)
        # Fetch batches until we have enough (or no more hits)
        local_offset = 0
        while len(out_docs) < limit and local_offset < 500:  # safety bound
            resp = explore_search(q, limit=per_call, offset=local_offset, sort=sort)
            docs = resp.get("docs", []) or []
            if not docs:
                break

            # optional year post-filter
            docs = _postfilter_by_year(docs, year_from, year_to)

            # dedupe by doc id
            for d in docs:
                rid = d.get("id") or (d.get("pnx", {}).get("control", {}).get("recordid") or [""])[0]
                if not rid or rid in seen:
                    continue
                seen.add(rid)
                out_docs.append(d)
                if len(out_docs) >= limit:
                    break

            local_offset += len(docs) if docs else per_call

        # reset offset baseline for the next rtype
        cur_offset = 0
        if len(out_docs) >= limit:
            break

    return {"docs": out_docs, "total": len(out_docs)}
