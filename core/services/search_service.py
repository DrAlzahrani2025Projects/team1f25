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
        peer_reviewed_only: bool = False,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Perform search using the library client."""
        try:
            logger.info(
                f"Performing library search - query: {query}, limit: {limit}, "
                f"type: {resource_type}, peer_reviewed: {peer_reviewed_only}"
            )
            logger.debug("SearchService.search - preparing to call library_client.search with params: %s", {"query": query, "limit": limit, "resource_type": resource_type})
            
            # Pass through optional date filters if supported by the client
            # Accept date_from/date_to as attributes on the SearchService call via kwargs
            # to keep backward compatibility.
            # If caller provided date_from/date_to as kwargs, use them; else None.
            results = self.library_client.search(
                query=query,
                limit=limit,
                offset=0,
                resource_type=resource_type,
                peer_reviewed_only=peer_reviewed_only,
                date_from=date_from,
                date_to=date_to,
            )

            logger.debug("SearchService.search - raw results received (type=%s)", type(results))
            
            if results:
                doc_count = len(results.get("docs", []))
                total_results = results.get("info", {}).get("total", 0)
                logger.info(f"Search returned {doc_count} docs, total available: {total_results}")
                logger.debug("SearchService.search - sample results keys: %s", list(results.keys()))
                
                # Log the tlevel facets for debugging
                if doc_count > 0:
                    first_doc = results["docs"][0]
                    tlevel = first_doc.get("pnx", {}).get("facets", {}).get("tlevel", [])
                    logger.info(f"First doc tlevel facets: {tlevel}")
                
                # Post-filter results if resource_type is specified
                if resource_type and doc_count > 0:
                    results = self._post_filter_by_resource_type(results, resource_type)
                    logger.info(f"After resource-type post-filter: {len(results.get('docs', []))} docs")
                
                # If peer_reviewed_only is True, post-filter results to ensure only peer-reviewed docs
                # TODO: Debug why post-filtering returns no results
                # if peer_reviewed_only and doc_count > 0:
                #     results = self._post_filter_peer_reviewed(results)
                #     logger.info(f"After peer-review post-filter: {len(results.get('docs', []))} docs")
            else:
                logger.warning("Search returned None or empty results")
                
            return results
        except Exception as e:
            logger.error(f"Library search error: {e}")
            return None
    
    def _post_filter_by_resource_type(self, results: Dict[str, Any], resource_type: str) -> Dict[str, Any]:
        """Post-filter results to keep only documents of the specified resource type."""
        if not results or "docs" not in results:
            return results
        
        docs = results.get("docs", [])
        filtered_docs = []
        
        # Map resource types to what might appear in the doc "type" field
        type_mappings = {
            "article": ["article", "journal article", "review"],
            "book": ["book", "ebook", "electronic book"],
            "journal": ["journal", "periodical"],
            "thesis": ["thesis", "dissertation"]
        }
        
        acceptable_types = type_mappings.get(resource_type.lower(), [resource_type.lower()])
        
        for idx, doc in enumerate(docs):
            pnx = doc.get("pnx", {})
            display = pnx.get("display", {})
            doc_type = display.get("type", [])
            
            if isinstance(doc_type, list) and doc_type:
                doc_type_str = doc_type[0].lower()
            else:
                doc_type_str = str(doc_type).lower()
            
            # Log for first few docs to debug
            if idx < 2:
                logger.info(f"Doc {idx} - raw type field: {doc_type}, parsed as: '{doc_type_str}'")
                # Also log all available display fields for first doc
                if idx == 0:
                    logger.info(f"Doc {idx} - all display keys: {list(display.keys())}")
            
            # Check if this document matches the requested resource type
            if any(acceptable in doc_type_str for acceptable in acceptable_types):
                filtered_docs.append(doc)
            else:
                if idx < 5:  # Log first 5 filtered-out docs
                    logger.debug(f"Filtering out doc {idx} with type '{doc_type_str}' (looking for {acceptable_types})")
        
        logger.info(f"Post-filter by resource type: {len(filtered_docs)} out of {len(docs)} docs match type '{resource_type}'")
        results["docs"] = filtered_docs
        return results
    
    def _post_filter_peer_reviewed(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Post-filter results to keep only peer-reviewed documents."""
        if not results or "docs" not in results:
            return results
        
        docs = results.get("docs", [])
        peer_reviewed_docs = []
        
        for doc in docs:
            pnx = doc.get("pnx", {})
            facets = pnx.get("facets", {})
            tlevel = facets.get("tlevel", [])
            
            # Check if this document is marked as peer-reviewed
            is_peer_reviewed = self._is_peer_reviewed(tlevel)
            if is_peer_reviewed:
                peer_reviewed_docs.append(doc)
            else:
                logger.debug(f"Filtering out non-peer-reviewed doc with tlevel: {tlevel}")
        
        logger.info(f"Post-filter: {len(peer_reviewed_docs)} out of {len(docs)} docs are peer-reviewed")
        results["docs"] = peer_reviewed_docs
        return results
    
    def _is_peer_reviewed(self, tlevel: list) -> bool:
        """Check if a document's tlevel facet indicates peer-reviewed status."""
        if not tlevel:
            return False
        for item in tlevel:
            if not item:
                continue
            val = item.lower().replace('-', ' ').replace('_', ' ')
            logger.debug(f"Checking tlevel value: {val}")
            if 'peer' in val and 'review' in val:
                return True
        return False
    
    def parse_results(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Parse search results using the formatter."""
        docs = results.get("docs", [])
        return [self.formatter.parse_document(doc) for doc in docs]


# Legacy function for backward compatibility - delegates to new service
def perform_library_search(
    query: str,
    limit: int = 20,
    resource_type: Optional[str] = None,
    peer_reviewed_only: bool = False,
    date_from: Optional[int] = None,
    date_to: Optional[int] = None,
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
            results = service.search(
                query=enhanced_query,
                limit=limit,
                resource_type=resource_type,
                peer_reviewed_only=peer_reviewed_only,
                date_from=date_from,
                date_to=date_to
            )
        else:
            # Normal search for articles and other types
            results = service.search(
                query=query,
                limit=limit,
                resource_type=resource_type,
                peer_reviewed_only=peer_reviewed_only,
                date_from=date_from,
                date_to=date_to
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
