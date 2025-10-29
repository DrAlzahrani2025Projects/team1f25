# core/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
# Define Pydantic models for agent input and output
class AgentInput(BaseModel):
    user_input: str
# Define ArticleBrief model
class ArticleBrief(BaseModel):
    record_id: str
    title: str = ""
    creators: List[str] = []
    creation_date: str = ""
    resource_type: str = "article"
    context: str = "PC"
    permalink: Optional[str] = None
# Define QAHit model
class QAHit(BaseModel):
    text: str
    meta: Dict[str, Any] = {}
# Define AgentOutput model
class AgentOutput(BaseModel):
    text: str
    list_items: List[str] = []
    hits: List[QAHit] = []
    # NEW: allow app to render and export later
    briefs: List[ArticleBrief] = []
    await_export: bool = False
