from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AgentInput(BaseModel):
    user_input: str

class ArticleBrief(BaseModel):
    record_id: str
    title: str = ""
    creators: List[str] = []
    creation_date: str = ""
    resource_type: str = "article"
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
    briefs: List[ArticleBrief] = []
    await_export: bool = False
