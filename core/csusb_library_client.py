# core/csusb_library_client.py
from __future__ import annotations
import os, json
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PRIMO_PUBLIC_BASE = os.getenv("PRIMO_PUBLIC_BASE", "https://csu-sb.primo.exlibrisgroup.com/primaws/rest/pub")
PRIMO_VID   = os.getenv("PRIMO_VID",   "01CALS_USB:01CALS_USB")
PRIMO_TAB   = os.getenv("PRIMO_TAB",   "CSUSB_CSU_Articles")
PRIMO_SCOPE = os.getenv("PRIMO_SCOPE", "CSUSB_CSU_articles")
PRIMO_INST  = os.getenv("PRIMO_INST",  "01CALS_USB")
DATA_DIR    = os.getenv("DATA_DIR", "/data")
PRIMO_TIMEOUT = int(os.getenv("PRIMO_PUBLIC_TIMEOUT", "20"))

def _session() -> requests.Session:
    s = requests.Session()
    r = Retry(total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=r))
    s.headers.update({"Accept": "application/json", "User-Agent": "ScholarAI/Week2-Retrieval"})
    return s

S = _session()

def build_q(any_query: str, *, lang_code: str|None, peer_reviewed: bool, rtype: str|None) -> str:
    parts = [f"any,contains,{any_query}"]
    if lang_code:
        parts.append(f"lang,exact,{lang_code}")
    if peer_reviewed:
        parts.append("tlevel,exact,peer_reviewed")
    if rtype:
        parts.append(f"rtype,exact,{rtype}")
    return ",AND;".join(parts)

def explore_search(q: str | None = None, limit: int = 10, offset: int = 0, *, query: str | None = None, sort: str = "rank") -> Dict[str, Any]:
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
    if r.status_code >= 400:
        raise requests.HTTPError(f"Explore {r.status_code}: {r.text[:400]}")
    return r.json()

def search_with_filters(*, query: str, limit: int, lang_code: str = "eng", peer_reviewed: bool = False,
                        rtypes: Optional[List[str]] = None, year_from: int = 1900, year_to: int = 2100,
                        sort: str = "rank") -> Dict[str, Any]:
    rtypes = rtypes or ["articles"]
    seen, out = set(), []
    for rt in rtypes:
        q = build_q(query, lang_code=lang_code, peer_reviewed=peer_reviewed, rtype=rt)
        resp = explore_search(q=q, limit=limit, sort=sort)
        docs = resp.get("docs", []) or []
        for d in docs:
            rid = d.get("id") or (d.get("pnx", {}).get("control", {}).get("recordid") or [""])[0]
            year = (d.get("pnx", {}).get("sort", {}).get("creationdate") or [""])[0]
            try: y = int(str(year)[:4]) if year else None
            except Exception: y = None
            if y and (y < year_from or y > year_to):
                continue
            if rid and rid not in seen:
                seen.add(rid)
                out.append(d)
            if len(out) >= limit:
                break
        if len(out) >= limit:
            break
    return {"docs": out, "total": len(out)}

def _cache_path(record_id: str, ctx: str) -> str:
    d = os.path.join(DATA_DIR, "primo", "cache", ctx or "PC")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{record_id}.json")

def fetch_full_with_fallback(record_id: str, context_hint: Optional[str] = None) -> Dict[str, Any]:
    for ctx in [context_hint, "L", "PC"]:
        if not ctx: continue
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
            try: json.dump(data, open(p, "w", encoding="utf-8"))
            except Exception: pass
            return data
    raise RuntimeError(f"Could not fetch PNX for {record_id}")
