# core/search_service.py
"""
Search service module for handling library searches and result processing.
"""
from typing import Dict, Any, Optional
from core.csusb_library_client import explore_search
from core.logging_utils import get_logger

logger = get_logger(__name__)


def perform_library_search(
    query: str, 
    limit: int = 20, 
    resource_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Perform search using the CSUSB library client."""
    try:
        logger.info(f"Performing library search with query: {query}, limit: {limit}, type: {resource_type}")
        
        # Pass resource_type to API for filtering at the source
        results = explore_search(q=query, limit=limit, offset=0, resource_type=resource_type)
        
        # Debug logging
        if results:
            doc_count = len(results.get("docs", []))
            total_results = results.get("info", {}).get("total", 0)
            logger.info(f"API returned {doc_count} docs, total available: {total_results}")
            logger.info(f"Returning {len(results.get('docs', []))} results to user")
        else:
            logger.warning("API returned None or empty results")
            
        return results
    except Exception as e:
        logger.error(f"Library search error: {e}")
        return None


def filter_by_resource_type(docs: list, resource_type: str) -> list:
    """Filter documents by resource type."""
    resource_type_lower = resource_type.lower()
    
    # Map common terms to what Primo actually uses
    type_mappings = {
        "article": ["article", "journal article", "review"],
        "book": ["book", "ebook", "electronic book"],
        "journal": ["journal", "periodical"],
        "thesis": ["thesis", "dissertation"],
    }
    
    # Get acceptable types for this resource type
    acceptable_types = type_mappings.get(resource_type_lower, [resource_type_lower])
    
    filtered = []
    for doc in docs:
        doc_type = parse_article_data(doc).get("type", "").lower()
        if any(acceptable in doc_type for acceptable in acceptable_types):
            filtered.append(doc)
    
    return filtered


def parse_article_data(doc: Dict[str, Any]) -> Dict[str, str]:
    """Parse article data from Primo API response."""
    pnx = doc.get("pnx", {})
    display = pnx.get("display", {})
    addata = pnx.get("addata", {})
    control = pnx.get("control", {})
    
    # Helper function to get first item from list or return default
    def first_or_default(data, key, default="N/A"):
        val = data.get(key, [])
        return val[0] if isinstance(val, list) and val else default
    
    # Construct proper discovery link
    context = doc.get("context", "L")
    record_id = first_or_default(control, "recordid", "")
    
    if record_id and record_id != "N/A":
        # Construct the proper discovery URL
        link = (
            f"https://csu-sb.primo.exlibrisgroup.com/discovery/fulldisplay"
            f"?context={context}"
            f"&vid=01CALS_USB:01CALS_USB"
            f"&search_scope=CSUSB_CSU_articles"
            f"&tab=CSUSB_CSU_Articles"
            f"&docid={record_id}"
        )
    else:
        link = ""
    
    # Get date with fallback
    date = first_or_default(display, "creationdate")
    if not date or date == "N/A":
        date = first_or_default(addata, "date")
    
    # Extract only year (YYYY format)
    year = "N/A"
    if date and date != "N/A":
        # Extract 4-digit year from date string
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', date)
        if year_match:
            year = year_match.group(0)
    
    return {
        "title": first_or_default(display, "title"),
        "author": first_or_default(display, "creator"),
        "date": year,
        "type": first_or_default(display, "type"),
        "source": first_or_default(display, "source"),
        "publisher": first_or_default(addata, "pub"),
        "issn": first_or_default(addata, "issn"),
        "doi": first_or_default(addata, "doi"),
        "link": link,
    }
