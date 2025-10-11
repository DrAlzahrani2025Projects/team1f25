# app/ingest/primo_explore_ingest.py
import argparse, sys
from typing import List
from tqdm import tqdm
import requests

from .primo_explore_client import explore_search, explore_get_record
from .primo_schema import PrimoFull, brief_from_doc
from .primo_store import append_records

def main():
    ap = argparse.ArgumentParser(description="Ingest CSUSB OneSearch via public Explore API → /data/primo/records.jsonl")
    ap.add_argument("--q", required=True, help="Free-text query (e.g., 'ott subscriber churn')")
    ap.add_argument("--limit", type=int, default=20, help="Total records to fetch")
    ap.add_argument("--page-size", type=int, default=10, help="Page size (<=50)")
    args = ap.parse_args()

    fetched = 0
    offset = 0
    out: List[PrimoFull] = []

    try:
        while fetched < args.limit:
            batch = min(args.page_size, args.limit - fetched)
            resp = explore_search(query=args.q, limit=batch, offset=offset)
            docs = resp.get("docs", [])
            if not docs:
                break
            for d in docs:
                brief = brief_from_doc(d)
                # Optionally fetch full record for richer metadata
                try:
                    full = explore_get_record(brief.record_id, context=brief.context or "PC")
                    pf = PrimoFull(brief=brief, pnx=full.get("pnx", {}), links=full.get("link", {}), raw=full)
                except Exception:
                    pf = PrimoFull(brief=brief, pnx=d.get("pnx", {}), links=d.get("link", {}), raw=d)
                out.append(pf)
            fetched += len(docs)
            offset += len(docs)

        wrote = append_records(out, dedupe=True)
        print(f"Wrote {wrote} new records to /data/primo/records.jsonl (fetched {len(out)})")

    except requests.HTTPError as e:
        print("\n--- Explore API error ---", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
