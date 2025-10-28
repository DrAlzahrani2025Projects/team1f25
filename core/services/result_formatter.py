"""
Result formatting service for library search results.
Follows SRP - Single Responsibility: Format and parse search results.
"""
import re
from typing import Dict, Any, List
from core.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ResultFormatter:
    """Handles formatting and parsing of library search results."""
    
    # Resource type mappings for filtering
    RESOURCE_TYPE_MAPPINGS = {
        "article": ["article", "journal article", "review"],
        "book": ["book", "ebook", "electronic book"],
        "journal": ["journal", "periodical"],
        "thesis": ["thesis", "dissertation"],
    }
    
    @staticmethod
    def parse_document(doc: Dict[str, Any]) -> Dict[str, str]:
        """Parse a single document from Primo API response."""
        pnx = doc.get("pnx", {})
        display = pnx.get("display", {})
        addata = pnx.get("addata", {})
        control = pnx.get("control", {})
        facets = pnx.get("facets", {})
        record_id = ResultFormatter._get_first_value(control, "recordid", "")
        logger.debug("parse_document - parsing doc recordid=%s", record_id)
        
        # Extract basic fields
        title = ResultFormatter._get_first_value(display, "title")
        author = ResultFormatter._get_first_value(display, "creator")
        doc_type = ResultFormatter._get_first_value(display, "type")
        source = ResultFormatter._get_first_value(display, "source")
        publisher = ResultFormatter._get_first_value(addata, "pub")
        issn = ResultFormatter._get_first_value(addata, "issn")
        doi = ResultFormatter._get_first_value(addata, "doi")
        
        # Extract and format date
        year = ResultFormatter._extract_year(display, addata)
        
        # Build discovery link
        link = ResultFormatter._build_discovery_link(doc, control)

        # Determine peer review status (be tolerant of variants: 'peer_reviewed', 'peer-reviewed', 'Peer Reviewed')
        tlevel = facets.get("tlevel", [])
        is_peer_reviewed = ResultFormatter._is_peer_reviewed_from_facets(tlevel)

        return {
            "title": title,
            "author": author,
            "date": year,
            "type": doc_type,
            "source": source,
            "publisher": publisher,
            "issn": issn,
            "doi": doi,
            "link": link,
            "peer_reviewed": "Yes" if is_peer_reviewed else "No",
        }

    @staticmethod
    def _is_peer_reviewed_from_facets(tlevel: List[str]) -> bool:
        """Return True if any facet entry indicates peer-reviewed status (tolerant to variants)."""
        if not tlevel:
            return False
        for item in tlevel:
            if not item:
                continue
            val = item.lower().replace('-', ' ').replace('_', ' ')
            if 'peer' in val and 'review' in val:
                return True
        return False
    
    @staticmethod
    def _get_first_value(data: Dict, key: str, default: str = "N/A") -> str:
        """Get first item from list or return default."""
        val = data.get(key, [])
        return val[0] if isinstance(val, list) and val else default
    
    @staticmethod
    def _extract_year(display: Dict, addata: Dict) -> str:
        """Extract year from date fields."""
        # Try display date first, then addata
        date = ResultFormatter._get_first_value(display, "creationdate")
        if not date or date == "N/A":
            date = ResultFormatter._get_first_value(addata, "date")
        
        # Extract 4-digit year
        if date and date != "N/A":
            year_match = re.search(r'\b\d{4}\b', date)
            if year_match:
                return year_match.group(0)
        
        return "N/A"
    
    @staticmethod
    def _build_discovery_link(doc: Dict, control: Dict) -> str:
        """Build the proper Primo discovery URL."""
        context = doc.get("context", "L")
        record_id = ResultFormatter._get_first_value(control, "recordid", "")
        
        if record_id and record_id != "N/A":
            return (
                f"https://csu-sb.primo.exlibrisgroup.com/discovery/fulldisplay"
                f"?context={context}"
                f"&vid=01CALS_USB:01CALS_USB"
                f"&search_scope=CSUSB_CSU_articles"
                f"&tab=CSUSB_CSU_Articles"
                f"&docid={record_id}"
            )
        return ""
    
    @staticmethod
    def filter_by_resource_type(docs: List[Dict], resource_type: str) -> List[Dict]:
        """Filter documents by resource type."""
        resource_type_lower = resource_type.lower()
        acceptable_types = ResultFormatter.RESOURCE_TYPE_MAPPINGS.get(
            resource_type_lower, 
            [resource_type_lower]
        )
        
        filtered = []
        for doc in docs:
            doc_data = ResultFormatter.parse_document(doc)
            doc_type = doc_data.get("type", "").lower()
            if any(acceptable in doc_type for acceptable in acceptable_types):
                filtered.append(doc)
        
        return filtered
    
    @staticmethod
    def format_table_data(docs: List[Dict]) -> List[Dict[str, Any]]:
        """Format documents for table display."""
        logger.debug("format_table_data - formatting %d docs", len(docs))
        table_data = []
        for idx, doc in enumerate(docs, 1):
            article = ResultFormatter.parse_document(doc)
            
            # Truncate long fields
            title = article["title"]
            if len(title) > 80:
                title = title[:80] + "..."
            
            author = article["author"]
            if len(author) > 40:
                author = author[:40] + "..."
            
            link = article.get("link", "")
            
            table_data.append({
                "#": idx,
                "Title": title,
                "Authors": author,
                "Year": article["date"],
                "Type": article["type"],
                "Link": link if link else None
            })
        
        return table_data
