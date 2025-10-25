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
    
    # Format query for Primo API if not already formatted
    # Primo expects format like: any,contains,search terms
    if not q.startswith("any,") and not q.startswith("title,") and not q.startswith("creator,"):
        q = f"any,contains,{q}"
    
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
    
    # Log response info for debugging
    doc_count = len(data.get("docs", []))
    total = data.get("info", {}).get("total", 0)
    _log.info(f"Primo returned {doc_count} docs out of {total} total results")
    
    return data