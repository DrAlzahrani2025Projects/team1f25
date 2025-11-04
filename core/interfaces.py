"""
Interface definitions for dependency inversion (SOLID principle).
These abstract base classes define contracts that concrete implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Iterable

# Interface for Language Model clients
class ILLMClient(ABC):
    """Interface for Language Model clients."""
    
    @abstractmethod
    def chat(
        self,
        content: Union[str, List[Dict[str, str]]],
        system: Optional[str] = None,
        **extra: Any
    ) -> str:
        """Send a chat request and get a response."""
        pass
    
    @abstractmethod
    def chat_stream(
        self,
        content: Union[str, List[Dict[str, str]]],
        system: Optional[str] = None,
        **extra: Any
    ) -> Iterable[str]:
        """Send a streaming chat request."""
        pass

# Interface for embedding model clients
class ILibraryClient(ABC):
    """Interface for library search clients."""
    
    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search the library database."""
        pass

# Interface for prompt providers
class IPromptProvider(ABC):
    """Interface for providing AI prompts."""
    
    @abstractmethod
    def get_follow_up_prompt(self) -> str:
        """Get the system prompt for follow-up questions."""
        pass
    
    @abstractmethod
    def get_parameter_extraction_prompt(self, conversation_text: str) -> str:
        """Get the prompt for extracting search parameters."""
        pass
    
    @abstractmethod
    def get_suggestion_prompt(self, query: str) -> str:
        """Get the prompt for generating search suggestions."""
        pass
