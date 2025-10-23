# core/utils.py
import os
import re

PRIMO_VID = os.getenv("PRIMO_VID", "01CALS_USB:01CALS_USB")
PRIMO_BASE = os.getenv("PRIMO_DISCOVERY_BASE", "https://csu-sb.primo.exlibrisgroup.com")
CURRENT_YEAR = int(os.getenv("CURRENT_YEAR_OVERRIDE", "0")) or __import__("datetime").datetime.utcnow().year

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
    # Remove date range and peer-review phrases from the generic terms
    t = re.sub(r"\b(from|between)\s+\d{4}\s+(to|and)\s+\d{4}\b", " ", t, flags=re.I)
    t = re.sub(r"\b(since|after|before)\s+\d{4}\b", " ", t, flags=re.I)
    t = re.sub(r"\blast\s+\d{1,2}\s+years\b", " ", t, flags=re.I)
    t = re.sub(r"\bpeer[-\s]?reviewed\b", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()

def strip_to_authors(utterance: str) -> list[str]:
    """Extract author names from an utterance.

    Supports patterns like:
    - by Jane Doe and John Smith
    - author: Turing, Alan
    - authors: Andrew Ng, Yann LeCun

    Returns a list of author strings (cleaned), possibly empty.
    """
    s = (utterance or "").strip()
    out: list[str] = []
    try:
        # author: ... (singular, keep commas inside the name)
        m_auth = re.search(r"\bauthor\s*:\s*(.+)$", s, re.I)
        if m_auth:
            segment = m_auth.group(1)
            segment = re.split(r"\b(on|about|regarding|for)\b", segment, flags=re.I)[0]
            parts = re.split(r"\s+and\s+", segment)
            for p in parts:
                name = p.strip().strip(".;:|/")
                if name:
                    out.append(name)
            return out
        # authors: ... (plural, split by comma and 'and')
        m_auths = re.search(r"\bauthors\s*:\s*(.+)$", s, re.I)
        segment = m_auths.group(1) if m_auths else None
        if segment is None:
            # by Jane Doe ... (stop at common delimiters)
            m2 = re.search(r"\bby\s+(.+)$", s, re.I)
            if m2:
                segment = m2.group(1)
        if segment:
            # Trim any trailing instruction words
            segment = re.split(r"\b(on|about|regarding|for)\b", segment, flags=re.I)[0]
            # Remove date range and unrelated qualifiers from the author segment
            segment = re.sub(r"\b(from|between)\s+\d{4}\s+(to|and)\s+\d{4}\b", " ", segment, flags=re.I)
            segment = re.sub(r"\b(since|after|before)\s+\d{4}\b", " ", segment, flags=re.I)
            segment = re.sub(r"\blast\s+\d{1,2}\s+years\b", " ", segment, flags=re.I)
            segment = re.sub(r"\bpeer[-\s]?reviewed\b", " ", segment, flags=re.I)
            # Split by 'and' or comma (only for plural/authors/by cases)
            parts = re.split(r"\s+and\s+|,", segment)
            for p in parts:
                name = p.strip().strip(".;:|/")
                # Discard stray numeric tokens (e.g., years) and empties
                if name and not re.fullmatch(r"\d{1,4}", name):
                    out.append(name)
    except Exception:
        pass
    return out

def parse_date_range(utterance: str, default_from: int = 1900, default_to: int = 2100) -> tuple[int, int]:
    """Parse a year range from text.

    Recognizes:
    - since 2019 => (2019, default_to)
    - from 2015 to 2021 / between 2015 and 2021 => (2015, 2021)
    - after 2010 => (2011, default_to)
    - before 2000 => (default_from, 1999)
    - last 5 years => (CURRENT_YEAR-4, CURRENT_YEAR)
    Falls back to (default_from, default_to).
    """
    s = (utterance or "").lower()
    yf, yt = default_from, default_to
    try:
        m = re.search(r"since\s+(\d{4})", s)
        if m:
            yf = int(m.group(1))
            return (yf, yt)
        m = re.search(r"(?:from|between)\s+(\d{4})\s+(?:to|and)\s+(\d{4})", s)
        if m:
            yf, yt = int(m.group(1)), int(m.group(2))
            if yt < yf:
                yf, yt = yt, yf
            return (yf, yt)
        m = re.search(r"after\s+(\d{4})", s)
        if m:
            yf = int(m.group(1)) + 1
            return (yf, yt)
        m = re.search(r"before\s+(\d{4})", s)
        if m:
            yt = int(m.group(1)) - 1
            return (yf, yt)
        m = re.search(r"last\s+(\d{1,2})\s+years", s)
        if m:
            n = int(m.group(1))
            end = CURRENT_YEAR
            start = max(default_from, end - max(1, n) + 1)
            return (start, end)
        # Single year mention "in 2018" or just a year => pin to that year
        m = re.search(r"\b(\d{4})\b", s)
        if m:
            y = int(m.group(1))
            return (y, y)
    except Exception:
        pass
    return (yf, yt)

def parse_peer_review_flag(utterance: str) -> bool:
    """Detect if the user asked for peer-reviewed content.

    Returns True if phrases like 'peer reviewed' or 'peer-reviewed' are present.
    Returns False otherwise.
    """
    s = (utterance or "").lower()
    # Optionally detect negatives (not peer reviewed)
    if re.search(r"not\s+peer[-\s]?reviewed", s):
        return False
    if re.search(r"peer[-\s]?reviewed", s):
        return True
    return False

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
