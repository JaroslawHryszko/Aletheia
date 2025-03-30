from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from aletheia.core import memory

router = APIRouter()

# === Models ===

class ThoughtRequest(BaseModel):
    content: str
    metadata: Optional[dict] = {}

class ThoughtResponse(BaseModel):
    timestamp: str
    thought: str
    meta: dict

# === Endpoints ===

@router.post("/", response_model=ThoughtResponse)
def add_thought(request: ThoughtRequest):
    try:
        entry = memory.save_thought(request.content, request.metadata)
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar", response_model=List[ThoughtResponse])
def find_similar_thoughts(q: str = Query(..., min_length=3), top_k: int = 5):
    try:
        results = memory.search_similar_thoughts(q, top_k=top_k)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
def get_recent_thoughts(limit: int = Query(10, ge=1, le=100)):
    try:
        thoughts = memory.load_thoughts()
        return list(reversed(thoughts[-limit:]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
