# core/services/search_service.py
"""
Search service module for handling library searches and result processing.
Refactored to follow SOLID principles with dependency injection.
"""
from typing import Dict, Any, Optional, List
from core.interfaces import ILibraryClient
from core.services.result_formatter import ResultFormatter
from core.utils.logging_utils import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service for performing library searches with proper separation of concerns."""
    
    def __init__(self, library_client: ILibraryClient, formatter: ResultFormatter = None):
        """Initialize with dependencies (Dependency Injection)."""
        self.library_client = library_client
        self.formatter = formatter or ResultFormatter()
    
    def search(
        self, 
        query: str, 
        limit: int = 20, 
        resource_type: Optional[str] = None,
        peer_reviewed_only: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Perform search using the library client."""
        try:
            logger.info(
                f"Performing library search - query: {query}, limit: {limit}, "
                f"type: {resource_type}, peer_reviewed: {peer_reviewed_only}"
            )
            
            results = self.library_client.search(
                query=query, 
                limit=limit, 
                offset=0, 
                resource_type=resource_type,
                peer_reviewed_only=peer_reviewed_only
            )
            
            if results:
                doc_count = len(results.get("docs", []))
                total_results = results.get("info", {}).get("total", 0)
                logger.info(f"Search returned {doc_count} docs, total available: {total_results}")
            else:
                logger.warning("Search returned None or empty results")
                
            return results
        except Exception as e:
            logger.error(f"Library search error: {e}")
            return None
    
    def parse_results(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Parse search results using the formatter."""
        docs = results.get("docs", [])
        return [self.formatter.parse_document(doc) for doc in docs]


# Legacy function for backward compatibility - delegates to new service
def perform_library_search(
    query: str, 
    limit: int = 20, 
    resource_type: Optional[str] = None,
    peer_reviewed_only: bool = False
) -> Optional[Dict[str, Any]]:
    """Legacy function - delegates to SearchService for backward compatibility."""
    try:
        from core.clients.csusb_library_client import CSUSBLibraryClient
        client = CSUSBLibraryClient()
        service = SearchService(client)
        
        # For books, we should adapt the query to find scholarly/academic books
        # when peer_reviewed_only is requested
        if peer_reviewed_only and resource_type and resource_type.lower() == "book":
            # Add academic/scholarly terms to the query
            academic_terms = ["academic", "scholarly", "research"]
            enhanced_query = f"{query} {' OR '.join(academic_terms)}"
            logger.info(f"Enhanced book query for peer-review: {enhanced_query}")
            results = client.search(
                query=enhanced_query,
                limit=limit,
                offset=0,
                resource_type=resource_type,
                peer_reviewed_only=peer_reviewed_only
            )
        else:
            # Normal search for articles and other types
            results = client.search(
                query=query,
                limit=limit,
                offset=0,
                resource_type=resource_type,
                peer_reviewed_only=peer_reviewed_only
            )
        
        if isinstance(results, dict) and results.get("docs"):
            doc_count = len(results["docs"])
            total = results.get("info", {}).get("total", 0)
            logger.info(f"Search returned {doc_count} docs out of {total} total")
            logger.info(f"First doc facets: {results['docs'][0].get('pnx', {}).get('facets', {}) if results['docs'] else 'No docs'}")
        return results
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {"_error": str(e)}


# Legacy function for backward compatibility
def parse_article_data(doc: Dict[str, Any]) -> Dict[str, str]:
    """Legacy function - delegates to ResultFormatter."""
    return ResultFormatter.parse_document(doc)


# Legacy function for backward compatibility
def filter_by_resource_type(docs: list, resource_type: str) -> list:
    """Legacy function - delegates to ResultFormatter."""
    return ResultFormatter.filter_by_resource_type(docs, resource_type)
