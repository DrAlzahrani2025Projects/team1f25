# agents/retrieval_agent.py
from typing import List, Dict, Any
from core.schemas import ArticleBrief
from core.logging_utils import get_logger
from core.utils import fulldisplay_link
from core.csusb_library_client import search_with_filters, fetch_full_with_fallback
from core.jsonl_store import append_records

_log = get_logger(__name__)

def _brief_from_doc(d: Dict[str, Any]) -> ArticleBrief:
    rid = d.get("id") or (d.get("pnx", {}).get("control", {}).get("recordid") or [""])[0]
    disp = d.get("pnx", {}).get("display", {}) or {}
    sort = d.get("pnx", {}).get("sort", {}) or {}
    link = d.get("link", {}) or {}
    permalink = link.get("record")
    creators = disp.get("creator") or []
    title = (disp.get("title") or [""])[0] if isinstance(disp.get("title"), list) else (disp.get("title") or "")
    date = (sort.get("creationdate") or [""])[0] if isinstance(sort.get("creationdate"), list) else (sort.get("creationdate") or "")
    ctx = (d.get("context") or "PC")
    return ArticleBrief(
        record_id=str(rid),
        title=title or "Untitled",
        creators=creators or [],
        creation_date=str(date or ""),
        resource_type="article",
        context=ctx,
        permalink=permalink or fulldisplay_link(str(rid), context=ctx),
    )

def search_articles(query: str, n: int = 10, peer_reviewed: bool = False,
                    sort: str = "rank", year_from: int = 1900, year_to: int = 2100) -> List[ArticleBrief]:
    _log.info("Search start: query='%s' n=%d peer_reviewed=%s sort=%s yfrom=%s yto=%s", query, n, peer_reviewed, sort, year_from, year_to)
    resp = search_with_filters(
        query=query, limit=n, lang_code="eng", peer_reviewed=peer_reviewed,
        rtypes=["articles"], year_from=year_from, year_to=year_to, sort=sort
    )
    docs = resp.get("docs", []) or []
    briefs = [_brief_from_doc(d) for d in docs]
    _log.info("Search done: docs=%d briefs=%d", len(docs), len(briefs))
    return briefs

def fetch_pnx_for_briefs(briefs: List[ArticleBrief]) -> List[Dict[str, Any]]:
    _log.info("Fetch PNX start: briefs=%d", len(briefs))
    records: List[Dict[str, Any]] = []
    for b in briefs:
        try:
            full = fetch_full_with_fallback(b.record_id, context_hint=b.context)
            pnx = full.get("pnx", {}) or {}
            links = full.get("link", {}) or {}
            raw = full
        except Exception as e:
            _log.warning("Fetch PNX failed for id=%s ctx=%s: %s", b.record_id, b.context, e)
            # fallback to minimal
            pnx, links, raw = {}, {}, {}
        records.append({
            "id": b.record_id,
            "brief": b.model_dump(),
            "pnx": pnx,
            "links": links,
            "raw": raw or {},
        })
    _log.info("Fetch PNX done: records=%d", len(records))
    return records

def export_briefs_with_pnx(briefs: List[ArticleBrief]) -> int:
    """Fetch PNX for each brief and append (deduped) to /data/primo/records.jsonl."""
    _log.info("Export briefs start: briefs=%d", len(briefs))
    records = fetch_pnx_for_briefs(briefs)
    result = append_records(records)
    _log.info("Export briefs done: wrote=%d", result)
    return result
