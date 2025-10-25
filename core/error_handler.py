"""
Centralized error handling utilities.
Follows DRY principle - consistent error handling patterns across the application.
"""
import streamlit as st
from typing import Optional, Callable, Any
from core.logging_utils import get_logger

logger = get_logger(__name__)


class ErrorHandler:
    """Centralized error handling with consistent patterns."""
    
    @staticmethod
    def handle_api_error(error: Exception, user_message: str = None) -> None:
        """Handle API-related errors with user-friendly messages."""
        default_message = "An error occurred while communicating with the service. Please try again."
        message = user_message or default_message
        
        logger.error(f"API Error: {error}")
        st.error(message)
    
    @staticmethod
    def handle_validation_error(error: Exception, user_message: str = None) -> None:
        """Handle validation errors."""
        default_message = "Invalid input. Please check your request and try again."
        message = user_message or default_message
        
        logger.warning(f"Validation Error: {error}")
        st.warning(message)
    
    @staticmethod
    def handle_not_found(resource: str, identifier: str = None) -> None:
        """Handle resource not found scenarios."""
        message = f"No {resource} found"
        if identifier:
            message += f" for '{identifier}'"
        message += "."
        
        logger.info(f"Not Found: {message}")
        st.warning(message)
    
    @staticmethod
    def safe_execute(
        func: Callable,
        *args,
        error_message: str = None,
        fallback_value: Any = None,
        **kwargs
    ) -> Any:
        """
        Safely execute a function with automatic error handling.
        Returns fallback_value if an error occurs.
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            if error_message:
                st.error(error_message)
            return fallback_value
    
    @staticmethod
    def log_and_display(
        message: str,
        level: str = "info",
        display_to_user: bool = True
    ) -> None:
        """
        Log a message and optionally display it to the user.
        
        Args:
            message: The message to log/display
            level: Log level ('info', 'warning', 'error')
            display_to_user: Whether to show in Streamlit UI
        """
        # Log the message
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)
        
        # Display to user if requested
        if display_to_user:
            if level == "error":
                st.error(message)
            elif level == "warning":
                st.warning(message)
            elif level == "success":
                st.success(message)
            else:
                st.info(message)


class SearchErrorHandler:
    """Specialized error handler for search operations."""
    
    @staticmethod
    def handle_empty_query() -> None:
        """Handle empty search query."""
        message = "Please provide a search query."
        logger.warning("Empty search query attempted")
        st.warning(message)
    
    @staticmethod
    def handle_search_failure(query: str, error: Exception) -> None:
        """Handle search API failure."""
        message = f"Failed to search for '{query}'. Please try again or refine your search."
        logger.error(f"Search failed for query '{query}': {error}")
        st.error(message)
    
    @staticmethod
    def handle_no_results(query: str, resource_type: Optional[str] = None) -> str:
        """
        Generate message for no search results.
        Returns the message string for further customization.
        """
        message = f"No results found for '{query}'"
        if resource_type:
            message += f" (filtering by {resource_type}s)"
        message += "."
        
        logger.info(f"No results: {message}")
        return message
