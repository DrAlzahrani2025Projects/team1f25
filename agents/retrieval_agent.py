# agents/retrieval_agent.py
from typing import List, Dict, Any, Optional
import re
from core.schemas import SearchBrief
from core.logging_utils import get_logger
from core.utils import fulldisplay_link
from core.csusb_library_client import search_with_filters

_log = get_logger(__name__)

def _as_str_first(v: Any) -> str:
    """Return a safe string from possibly nested list values.

    Examples:
    - "book" -> "book"
    - ["book"] -> "book"
    - [["book"]] -> "book"
    - None -> ""
    """
    try:
        if v is None:
            return ""
        if isinstance(v, list):
            return _as_str_first(v[0]) if v else ""
        return str(v)
    except Exception:
        return ""


def _brief_from_doc(d: Dict[str, Any]) -> SearchBrief:
    rid = d.get("id") or (d.get("pnx", {}).get("control", {}).get("recordid") or [""])[0]
    pnx = d.get("pnx", {}) or {}
    disp = pnx.get("display", {}) or {}
    sort = pnx.get("sort", {}) or {}
    search_fields = pnx.get("search", {}) or {}
    link = d.get("link", {}) or {}
    permalink = link.get("record")
    creators = sort.get("author") or []
    title = (disp.get("title") or [""])[0] if isinstance(disp.get("title"), list) else (disp.get("title") or "")
    date = (sort.get("creationdate") or [""])[0] if isinstance(sort.get("creationdate"), list) else (sort.get("creationdate") or "")
    # Normalize date to year (YYYY) if possible
    year = str(date or "")
    try:
        m = re.search(r"(\d{4})", year)
        if m:
            year = m.group(1)
    except Exception:
        pass
    # Prefer search.rtype, fall back to display.type, default to 'article' for compatibility
    rtype = _as_str_first(search_fields.get("rtype")) or _as_str_first(disp.get("type")) or "article"
    ctx = (d.get("context") or "PC")
    return SearchBrief(
        record_id=str(rid),
        title=title or "Untitled",
        creators=creators or [],
        creation_date=year,
        resource_type=rtype,
        context=ctx,
        permalink=permalink or fulldisplay_link(str(rid), context=ctx),
    )

def search(query: str, n: int = 10, peer_reviewed: bool = False,
           sort: str = "rank", year_from: int = 1900, year_to: int = 2100,
           search_type: Optional[str] = None, authors: Optional[List[str]] = None) -> List[SearchBrief]:
    _log.info("Search start: query='%s' n=%d peer_reviewed=%s sort=%s yfrom=%s yto=%s", query, n, peer_reviewed, sort, year_from, year_to)
    rtypes = [search_type] if search_type else None
    resp = search_with_filters(
        query=query,
        limit=n,
        lang_code="eng",
        peer_reviewed=peer_reviewed,
        rtypes=rtypes,
        year_from=year_from,
        year_to=year_to,
        sort=sort,
        authors=authors,
    )
    docs = resp.get("docs", []) or []
    briefs = [_brief_from_doc(d) for d in docs]
    _log.info("Search done: docs=%d briefs=%d", len(docs), len(briefs))
    return briefs


# Backward-compatible alias expected by tests/other callers
def onesearch(query: str, n: int = 10, peer_reviewed: bool = False,
              sort: str = "rank", year_from: int = 1900, year_to: int = 2100,
              search_type: Optional[str] = None, authors: Optional[List[str]] = None) -> List[SearchBrief]:
    return search(
        query=query,
        n=n,
        peer_reviewed=peer_reviewed,
        sort=sort,
        year_from=year_from,
        year_to=year_to,
        search_type=search_type,
        authors=authors,
    )