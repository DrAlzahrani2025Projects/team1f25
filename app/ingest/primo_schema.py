# app/ingest/primo_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PrimoBrief(BaseModel):
    record_id: str
    context: str
    title: Optional[str] = None
    creators: List[str] = []
    creation_date: Optional[str] = None
    resource_type: Optional[str] = None
    permalink: Optional[str] = None
    source: Optional[str] = None
    holdings: Optional[Dict[str, Any]] = None

class PrimoFull(BaseModel):
    brief: PrimoBrief
    pnx: Dict[str, Any] = Field(default_factory=dict)
    links: Dict[str, Any] = Field(default_factory=dict)
    raw: Dict[str, Any] = Field(default_factory=dict)

def brief_from_doc(doc: Dict[str, Any]) -> PrimoBrief:
    pnx = doc.get("pnx", {})
    link = doc.get("link", {})
    # many fields are arrays; choose first display value
    title = (pnx.get("display", {}).get("title") or [""])[0]
    creators = pnx.get("display", {}).get("creator") or []
    creation_date = (pnx.get("sort", {}).get("creationdate") or [""])[0]
    resource_type = (pnx.get("display", {}).get("type") or [""])[0]
    permalink = (link.get("record") or [""])[0]
    source = (pnx.get("control", {}).get("sourceid") or [""])[0]
    record_id = doc.get("id") or (pnx.get("control", {}).get("recordid") or [""])[0]
    context = doc.get("context") or (pnx.get("control", {}).get("source") or ["PC"])[0]
    holdings = doc.get("delivery", {})
    return PrimoBrief(
        record_id=record_id,
        context=context,
        title=title,
        creators=creators,
        creation_date=creation_date,
        resource_type=resource_type,
        permalink=permalink,
        source=source,
        holdings=holdings,
    )
