# core/search_service.py
"""
Search service module for handling library searches and result processing.
"""
from typing import Dict, Any, Optional
from core.csusb_library_client import explore_search
from core.logging_utils import get_logger

logger = get_logger(__name__)


def perform_library_search(query: str, limit: int = 20) -> Optional[Dict[str, Any]]:
    """Perform search using the CSUSB library client."""
    try:
        logger.info(f"Performing library search with query: {query}")
        results = explore_search(q=query, limit=limit, offset=0)
        
        # Debug logging
        if results:
            doc_count = len(results.get("docs", []))
            total_results = results.get("info", {}).get("total", 0)
            logger.info(f"API returned {doc_count} docs, total available: {total_results}")
            logger.debug(f"Full API response keys: {results.keys()}")
        else:
            logger.warning("API returned None or empty results")
            
        return results
    except Exception as e:
        logger.error(f"Library search error: {e}")
        return None


def parse_article_data(doc: Dict[str, Any]) -> Dict[str, str]:
    """Parse article data from Primo API response."""
    pnx = doc.get("pnx", {})
    display = pnx.get("display", {})
    addata = pnx.get("addata", {})
    
    # Helper function to get first item from list or return default
    def first_or_default(data, key, default="N/A"):
        val = data.get(key, [])
        return val[0] if isinstance(val, list) and val else default
    
    return {
        "title": first_or_default(display, "title"),
        "author": first_or_default(display, "creator"),
        "date": first_or_default(display, "creationdate"),
        "type": first_or_default(display, "type"),
        "source": first_or_default(display, "source"),
        "publisher": first_or_default(addata, "pub"),
        "issn": first_or_default(addata, "issn"),
        "doi": first_or_default(addata, "doi"),
    }
