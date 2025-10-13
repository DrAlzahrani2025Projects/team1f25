from __future__ import annotations
from typing import List
from core.schemas import ArticleBrief
from core.utils import fulldisplay_link

def search_articles(query: str, n: int = 10, peer_reviewed: bool = False,
                    sort: str = "rank", year_from: int = 1900, year_to: int = 2100) -> List[ArticleBrief]:
    # Week 1 stub: return mock briefs so the orchestrator works end-to-end.
    briefs: List[ArticleBrief] = []
    for i in range(1, n + 1):
        rid = f"STUB-{i:03d}"
        briefs.append(ArticleBrief(
            record_id=rid,
            title=f"[stub] {query.title()} — Article {i}",
            creators=["Doe, Jane", "Doe, John"],
            creation_date="2023",
            permalink=fulldisplay_link(rid, context="PC"),
        ))
    return briefs

def fetch_pnx_for_briefs(briefs: List[ArticleBrief]):
    # Week 1 stub: no-op (real PNX in Week 2)
    return []
