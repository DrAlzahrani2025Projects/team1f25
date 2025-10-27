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
        resource_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Perform search using the library client."""
        try:
            logger.info(f"Performing library search - query: {query}, limit: {limit}, type: {resource_type}")
            logger.debug("SearchService.search - preparing to call library_client.search with params: %s", {"query": query, "limit": limit, "resource_type": resource_type})
            
            results = self.library_client.search(
                query=query, 
                limit=limit, 
                offset=0, 
                resource_type=resource_type
            )

            logger.debug("SearchService.search - raw results received (type=%s)", type(results))
            
            if results:
                doc_count = len(results.get("docs", []))
                total_results = results.get("info", {}).get("total", 0)
                logger.info(f"Search returned {doc_count} docs, total available: {total_results}")
                logger.debug("SearchService.search - sample results keys: %s", list(results.keys()))
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
    resource_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Legacy function - delegates to SearchService for backward compatibility."""
    from core.clients.csusb_library_client import CSUSBLibraryClient
    client = CSUSBLibraryClient()
    service = SearchService(client)
    return service.search(query, limit, resource_type)


# Legacy function for backward compatibility
def parse_article_data(doc: Dict[str, Any]) -> Dict[str, str]:
    """Legacy function - delegates to ResultFormatter."""
    return ResultFormatter.parse_document(doc)


# Legacy function for backward compatibility
def filter_by_resource_type(docs: list, resource_type: str) -> list:
    """Legacy function - delegates to ResultFormatter."""
    return ResultFormatter.filter_by_resource_type(docs, resource_type)
