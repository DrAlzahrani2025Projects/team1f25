# core/utils.py
import os, re

PRIMO_VID = os.getenv("PRIMO_VID", "01CALS_USB:01CALS_USB")
PRIMO_BASE = os.getenv("PRIMO_DISCOVERY_BASE", "https://csu-sb.primo.exlibrisgroup.com")

def detect_intent(utterance: str) -> str:
    u = utterance.lower()
    if any(w in u for w in ["list ", "top ", "find articles", "show articles", "search articles"]):
        return "LIST"
    return "ANSWER"

def extract_top_n(utterance: str, default: int = 10) -> int:
    m = re.search(r"\btop\s+(\d{1,3})\b", utterance, re.I)
    if not m: return default
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

def fulldisplay_link(record_id: str, context: str = "PC") -> str:
    return f"{PRIMO_BASE}/discovery/fulldisplay?vid={PRIMO_VID}&context={context}&docid={record_id}"
