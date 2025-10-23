# core/utils.py
import os
import re

PRIMO_VID = os.getenv("PRIMO_VID", "01CALS_USB:01CALS_USB")
PRIMO_BASE = os.getenv("PRIMO_DISCOVERY_BASE", "https://csu-sb.primo.exlibrisgroup.com")

def extract_top_n(utterance: str, default: int = 10) -> int:
    m = re.search(r"\btop\s+(\d{1,3})\b", utterance, re.I)
    if not m:
        return default
    try:
        n = int(m.group(1))
        return max(1, min(50, n))
    except Exception:
        return default

def strip_to_search_terms(utterance: str) -> str:
    t = re.sub(r"\b(list|show|find|retrieve)\b", " ", utterance, flags=re.I)
    t = re.sub(r"\b(top\s+\d+)\b", " ", t, flags=re.I)
    t = re.sub(r"\b(articles?|papers?|literature|references?)\b", " ", t, flags=re.I)
    t = t.replace("about", " ").replace("on", " ")
    return re.sub(r"\s+", " ", t).strip()

def strip_to_search_type(utterance: str) -> str:
    """Extract a resource type hint from an utterance.

                Supported canonical types (subset of common Primo rtypes):
                - articles, books, book_chapters, dissertations, conference_proceedings, videos,
                    journals, scores, datasets, images, maps, audio, newspaper_articles, patents,
                    reports, reviews, software, websites, reference_entries, government_documents

    Returns the canonical type string if found, otherwise an empty string.
    """
    s = (utterance or "").lower()

    # Order matters: check more specific phrases first
    patterns = [
        # More specific phrases first
        (r"\bconference\s+proceedings?\b|\bproceedings?\b", "conference_proceedings"),
        (r"\bbook\s+chapters?\b|\bchapters?\b", "book_chapters"),
        (r"\bdissertations?\b|\btheses\b|\bthesis\b", "dissertations"),
        (r"\bnewspaper\s+articles?\b|\bnews\s+articles?\b", "newspaper_articles"),
        (r"\b(reference|encyclopedia|encyclopaedia|dictionary)\s+(entries?|articles?)\b", "reference_entries"),
        (r"\bgovernment\s+(documents?|publications?)\b", "government_documents"),
        (r"\bpatents?\b", "patents"),
        (r"\breports?\b|\bwhite\s+papers?\b|\btech(nical)?\s+reports?\b", "reports"),
        (r"\breviews?\b(?!\s*of\s*systems?)", "reviews"),
        (r"\bdatasets?\b|\bdata\s+sets?\b", "datasets"),
        (r"\bsoftware\b|\bcode\b|\bpackages?\b", "software"),
        (r"\bweb\s*sites?\b|\bwebpages?\b|\bweb\s*pages?\b|\bweb\s*resources?\b", "websites"),
        (r"\bimages?\b|\bphotographs?\b|\bpictures?\b|\billustrations?\b", "images"),
        (r"\bmaps?\b|\batlases?\b", "maps"),
        (r"\baudio\b|\bpodcasts?\b|\bsound\s+recordings?\b", "audio"),
        # Core types
        (r"\barticles?\b|\bpaper(s)?\b", "articles"),
        (r"\bbooks?\b", "books"),
        (r"\bv(ideo|ideos)\b|\bfilms?\b|\bmovies?\b", "videos"),
        (r"\bjournals?\b|\bmagazines?\b", "journals"),
        (r"\bscores?\b|\bsheet\s+music\b", "scores"),
    ]
    for pat, canon in patterns:
        if re.search(pat, s, flags=re.I):
            return canon
    return ""

def fulldisplay_link(record_id: str, context: str = "PC") -> str:
    return f"{PRIMO_BASE}/discovery/fulldisplay?vid={PRIMO_VID}&context={context}&docid={record_id}"
