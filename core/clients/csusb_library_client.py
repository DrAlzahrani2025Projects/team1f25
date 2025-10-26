# core/clients/csusb_library_client.py
import json
import os
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from core.interfaces import ILibraryClient
from core.utils.logging_utils import get_logger
from core.utils.dates import normalize_date_bound

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


class CSUSBLibraryClient(ILibraryClient):
    """
    Client for CSUSB Library Primo API.
    Implements ILibraryClient interface for dependency inversion.
    """
    
    def __init__(
        self,
        base_url: str = PRIMO_PUBLIC_BASE,
        vid: str = PRIMO_VID,
        tab: str = PRIMO_TAB,
        scope: str = PRIMO_SCOPE,
        inst: str = PRIMO_INST,
        timeout: int = PRIMO_TIMEOUT
    ):
        """Initialize client with configuration."""
        self.base_url = base_url
        self.vid = vid
        self.tab = tab
        self.scope = scope
        self.inst = inst
        self.timeout = timeout
        self.session = S
    
    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        resource_type: Optional[str] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search the library database.
        Implements ILibraryClient.search() interface.
        """
        return self._explore_search(
            q=query,
            limit=limit,
            offset=offset,
            resource_type=resource_type,
            date_from=date_from,
            date_to=date_to,
        )
    
    def _explore_search(
        self,
        q: str | None = None,
        limit: int = 10,
        offset: int = 0,
        *,
        query: str | None = None,
        sort: str = "rank",
        resource_type: str | None = None,
        date_from: int | None = None,
        date_to: int | None = None,
    ) -> Dict[str, Any]:
        """Internal method for Primo search."""
        if (not q) and query:
            q = query
        if not q:
            raise ValueError("explore_search: missing q/query")
        
        # Format query for Primo API if not already formatted
        if not q.startswith("any,") and not q.startswith("title,") and not q.startswith("creator,"):
            q = f"any,contains,{q}"
        
        url = f"{self.base_url.rstrip('/')}/pnxs"
        params = {
            "vid": self.vid,
            "tab": self.tab,
            "scope": self.scope,
            "inst": self.inst,
            "q": q,
            "limit": str(min(50, max(1, limit))),
            "offset": str(max(0, offset)),
            "lang": "en",
            "mode": "advanced",
            "sort": sort,
            "skipDelivery": "Y",
            "rtaLinks": "true",
            "rapido": "true",
            "showPnx": "true",
        }
        
        # Add resource type facet filter if specified
        if resource_type:
            type_facets = {
                "article": "articles",
                "book": "books", 
                "journal": "journals",
                "thesis": "dissertations",
            }
            facet_value = type_facets.get(resource_type.lower(), resource_type.lower())
            params["qInclude"] = f"facet_rtype,exact,{facet_value}"
            _log.info(f"Adding resource type filter: {params['qInclude']}")

        # Add date range filter if specified (year or YYYYMMDD accepted)
        if date_from is not None or date_to is not None:
            from datetime import datetime

            # Normalize bounds using shared utility
            start_str = normalize_date_bound(date_from, True)
            end_str = normalize_date_bound(date_to, False)

            # Clamp future dates to today
            today = datetime.utcnow().strftime("%Y%m%d")
            try:
                if end_str and end_str.isdigit() and int(end_str) > int(today):
                    _log.info(f"Clamping end date {end_str} to today {today}")
                    end_str = today
                if start_str and start_str.isdigit() and int(start_str) > int(today):
                    _log.info(f"Clamping start date {start_str} to today {today}")
                    start_str = today
                # Swap if start > end
                if start_str and end_str and start_str.isdigit() and end_str.isdigit() and int(start_str) > int(end_str):
                    _log.info(f"Swapping start/end dates: {start_str} > {end_str}")
                    start_str, end_str = end_str, start_str
            except Exception:
                pass

            # Append date filter to the q parameter
            params_q = params.get("q", "")
            if params_q.endswith(";"):
                params_q = params_q.rstrip(";")
            date_segment = f"dr_s,exact,{start_str},AND;dr_e,exact,{end_str};"
            params["q"] = params_q + ";" + date_segment if params_q else date_segment
            _log.info(f"Adding date range filter to q: {params['q']}")
        
        r = self.session.get(url, params=params, timeout=self.timeout)
        _log.info("Primo explore_search URL: %s", r.url)
        
        if r.status_code >= 400:
            raise requests.HTTPError(f"Explore {r.status_code}: {r.text[:400]}")
        
        data = r.json()
        
        # Log response info
        doc_count = len(data.get("docs", []))
        total = data.get("info", {}).get("total", 0)
        _log.info(f"Primo returned {doc_count} docs out of {total} total results")
        
        return data


# Legacy function for backward compatibility

# Legacy function for backward compatibility
def explore_search(
    q: str | None = None,
    limit: int = 10,
    offset: int = 0,
    *,
    query: str | None = None,
    sort: str = "rank",
    resource_type: str | None = None,
    date_from: int | None = None,
    date_to: int | None = None,
) -> Dict[str, Any]:
    """Legacy function - delegates to CSUSBLibraryClient for backward compatibility."""
    client = CSUSBLibraryClient()
    return client._explore_search(
        q=q,
        limit=limit,
        offset=offset,
        query=query,
        sort=sort,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to
    )
