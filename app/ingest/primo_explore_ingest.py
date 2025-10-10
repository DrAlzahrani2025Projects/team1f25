# app/ingest/primo_explore_ingest.py
"""
CLI ingester for CSUSB OneSearch using the public Primo VE 'pub/pnxs' endpoint.

- Searches with the Explore/Discovery public API (no API key).
- For each brief search hit, fetches the FULL PNX using a context fallback:
    1) try the hinted context from the brief (if any),
    2) then 'L' (Local),
    3) then 'PC' (Primo Central).
- Writes normalized records to /data/primo/records.jsonl with dedupe by record_id.

Usage (inside container):
    python -m app.ingest.primo_explore_ingest --q "ott subscriber churn" --limit 20 --page-size 10
"""

from __future__ import annotations
import argparse
import sys
from typing import List

import requests
from tqdm import tqdm

from .primo_explore_client import (
    explore_search,
    fetch_full_with_fallback,  # robust per-record PNX fetch with context fallback
)
from .primo_schema import PrimoFull, brief_from_doc
from .primo_store import append_records


def ingest_query(query: str, limit: int = 20, page_size: int = 10) -> int:
    """
    Run a search and persist results with full PNX.
    Returns the number of NEW records written (after dedupe).
    """
    fetched_total = 0
    offset = 0
    out: List[PrimoFull] = []

    with tqdm(total=limit, desc="Fetching search results", unit="rec") as pbar:
        while fetched_total < limit:
            batch = min(page_size, limit - fetched_total)
            resp = explore_search(query=query, limit=batch, offset=offset)
            docs = resp.get("docs", [])
            if not docs:
                break

            for d in docs:
                brief = brief_from_doc(d)

                # Fetch full PNX with robust fallback across contexts
                try:
                    full = fetch_full_with_fallback(
                        record_id=brief.record_id,
                        context_hint=brief.context,
                    )
                    pnx = full.get("pnx", {})
                    links = full.get("link", {})
                    raw = full
                    # If (rarely) still empty, fall back to the search doc
                    if not pnx:
                        pnx = d.get("pnx", {})
                        links = d.get("link", {})
                        raw = d
                except Exception:
                    # Network or 404 – keep the brief doc as last resort
                    pnx = d.get("pnx", {})
                    links = d.get("link", {})
                    raw = d

                out.append(PrimoFull(brief=brief, pnx=pnx, links=links, raw=raw))
                fetched_total += 1
                pbar.update(1)
                if fetched_total >= limit:
                    break

            offset += len(docs)
            if not docs:
                break

    wrote = append_records(out, dedupe=True)
    return wrote


def main():
    ap = argparse.ArgumentParser(
        description="Ingest CSUSB OneSearch via public 'pub/pnxs' endpoint → /data/primo/records.jsonl (with full PNX)."
    )
    ap.add_argument("--q", required=True, help="Free-text query (e.g., 'ott subscriber churn')")
    ap.add_argument("--limit", type=int, default=20, help="Total records to fetch")
    ap.add_argument("--page-size", type=int, default=10, help="Page size per request (<=50)")
    args = ap.parse_args()

    try:
        wrote = ingest_query(query=args.q, limit=args.limit, page_size=args.page_size)
        print(f"Wrote {wrote} new records to /data/primo/records.jsonl")
        if wrote == 0:
            print("Note: 0 new writes (either no results, all duplicates, or failures).", file=sys.stderr)
    except requests.HTTPError as e:
        print("\n--- Explore/Public API error ---", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print("\n--- Unexpected error ---", file=sys.stderr)
        print(repr(e), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
