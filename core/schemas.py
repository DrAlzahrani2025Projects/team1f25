# core/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AgentInput(BaseModel):
    user_input: str

class SearchBreif(BaseModel):
    record_id: str
    title: str = ""
    creators: List[str] = []
    creation_date: str = ""
    # Optional: resource type hint (e.g., article, book, dissertation, etc.)
    resource_type: Optional[str] = None
    context: str = "PC"
    permalink: Optional[str] = None

class QAHit(BaseModel):
    text: str
    meta: Dict[str, Any] = {}

class AgentOutput(BaseModel):
    text: str
    list_items: List[str] = []
    hits: List[QAHit] = []
    # NEW: allow app to render and export later
    briefs: List[SearchBreif] = []
    await_export: bool = False
