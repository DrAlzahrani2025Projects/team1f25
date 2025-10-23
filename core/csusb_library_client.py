# core/csusb_library_client.py
import json
import os
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from core.logging_utils import get_logger

PRIMO_PUBLIC_BASE = os.getenv("PRIMO_PUBLIC_BASE", "https://csu-sb.primo.exlibrisgroup.com/primaws/rest/pub")
PRIMO_VID   = os.getenv("PRIMO_VID",   "01CALS_USB:01CALS_USB")
PRIMO_TAB   = os.getenv("PRIMO_TAB",   "CSUSB_CSU_Articles")
PRIMO_SCOPE = os.getenv("PRIMO_SCOPE", "CSUSB_CSU_articles")
PRIMO_INST  = os.getenv("PRIMO_INST",  "01CALS_USB")
DATA_DIR    = os.getenv("DATA_DIR", "/data")
if os.name == "posix" and (":" in DATA_DIR or DATA_DIR.startswith(("C:\\", "C:/"))):
    DATA_DIR = "/data"
PRIMO_TIMEOUT = int(os.getenv("PRIMO_PUBLIC_TIMEOUT", "20"))

def _session() -> requests.Session:
    s = requests.Session()
    r = Retry(total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=r))
    s.headers.update({"Accept": "application/json", "User-Agent": "ScholarAI/Week2-Retrieval"})
    return s

S = _session()
_log = get_logger(__name__)

def build_q(
    any_query: str,
    *,
    lang_code: str | None,
    peer_reviewed: bool,
    rtype: str | None,
    authors: Optional[List[str]] = None,
    dr_s: Optional[str] = None,
    dr_e: Optional[str] = None,
) -> str:
    parts = [f"any,contains,{any_query}"]
    # If authors provided, add creator clauses (ANDed)
    if authors:
        for a in authors:
            a = (a or "").strip()
            if a:
                parts.append(f"creator,contains,{a}")
    # Add date range as query clauses instead of URL params
    if dr_s:
        parts.append(f"dr_s,exact,{dr_s}")
    if dr_e:
        parts.append(f"dr_e,exact,{dr_e}")
    if lang_code:
        parts.append(f"lang,exact,{lang_code}")
    if peer_reviewed:
        parts.append("facet_tlevel,exact,peer_reviewed")
    if rtype:
        parts.append(f"rtype,exact,{rtype}")
    return ",AND;".join(parts)

def explore_search(
    q: str | None = None,
    limit: int = 10,
    offset: int = 0,
    *,
    query: str | None = None,
    sort: str = "rank",
) -> Dict[str, Any]:
    if (not q) and query:
        q = query
    if not q:
        raise ValueError("explore_search: missing q/query")
    url = f"{PRIMO_PUBLIC_BASE.rstrip('/')}/pnxs"
    params = {
        "vid": PRIMO_VID, "tab": PRIMO_TAB, "scope": PRIMO_SCOPE, "inst": PRIMO_INST,
        "q": q, "limit": str(min(50, max(1, limit))), "offset": str(max(0, offset)),
        "lang": "en", "mode": "advanced", "sort": sort,
        "skipDelivery": "Y", "rtaLinks": "true", "rapido": "true",
        "showPnx": "true",
    }
    r = S.get(url, params=params, timeout=PRIMO_TIMEOUT)
    _log.info("Primo explore_search URL: %s", r.url)
    if r.status_code >= 400:
        raise requests.HTTPError(f"Explore {r.status_code}: {r.text[:400]}")
    data = r.json()
    return data

def search_with_filters(*, query: str, limit: int, lang_code: Optional[str] = "eng", peer_reviewed: bool = False,
                        rtypes: Optional[List[Optional[str]]] = None, year_from: int = 1900, year_to: int = 2100,
                        sort: str = "rank", authors: Optional[List[str]] = None) -> Dict[str, Any]:
    # If rtypes is None, run a single pass without an rtype facet
    rtypes = rtypes if rtypes is not None else [None]
    seen, out = set(), []
    for rt in rtypes:
        # Build YYYYMMDD date range (inclusive)
        yf = int(year_from) if year_from is not None else None
        yt = int(year_to) if year_to is not None else None
        if yf is not None and yt is not None and yt < yf:
            yf, yt = yt, yf
        drs = f"{yf}0101" if yf is not None else None
        dre = f"{yt}1231" if yt is not None else None
        
        q = build_q(
            query,
            lang_code=lang_code,
            peer_reviewed=peer_reviewed,
            rtype=rt,
            authors=authors,
            dr_s=drs,
            dr_e=dre,
        )
        _log.info("Primo search q='%s' limit=%s sort=%s", q, limit, sort)
        resp = explore_search(q=q, limit=limit, sort=sort)
        docs = resp.get("docs", []) or []
        _log.info("Primo returned %d docs (pre-filter)", len(docs))
        for d in docs:
            rid = d.get("id") or (d.get("pnx", {}).get("control", {}).get("recordid") or [""])[0]
            if rid and rid not in seen:
                seen.add(rid)
                out.append(d)
            if len(out) >= limit:
                break
        if len(out) >= limit:
            break
    _log.info("Primo after filters: %d docs", len(out))
    return {"docs": out, "total": len(out)}

def _cache_path(record_id: str, ctx: str) -> str:
    d = os.path.join(DATA_DIR, "primo", "cache", ctx or "PC")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{record_id}.json")

def fetch_full_with_fallback(record_id: str, context_hint: Optional[str] = None) -> Dict[str, Any]:
    for ctx in [context_hint, "L", "PC"]:
        if not ctx:
            continue
        p = _cache_path(record_id, ctx)
        if os.path.exists(p):
            try:
                return json.load(open(p, encoding="utf-8"))
            except Exception:
                pass
        url = f"{PRIMO_PUBLIC_BASE.rstrip('/')}/pnxs/{ctx}/{record_id}"
        params = {"vid": PRIMO_VID, "lang": "en", "inst": PRIMO_INST, "tab": PRIMO_TAB, "scope": PRIMO_SCOPE}
        r = S.get(url, params=params, timeout=PRIMO_TIMEOUT)
        if r.ok:
            data = r.json()
            try:
                json.dump(data, open(p, "w", encoding="utf-8"))
            except Exception:
                pass
            return data
    raise RuntimeError(f"Could not fetch PNX for {record_id}")
