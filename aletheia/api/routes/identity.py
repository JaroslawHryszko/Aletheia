from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from aletheia.core import identity

router = APIRouter()

# === Pydantic Schemas ===

class GoalUpdateRequest(BaseModel):
    goal_key: str
    delta: float

# === Routes ===

@router.get("/")
def get_identity():
    try:
        return identity.load_identity()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update")
def update_goal_progress(request: GoalUpdateRequest):
    try:
        updated = identity.update_goal_progress(request.goal_key, request.delta)
        return {
            "message": f"Goal '{request.goal_key}' updated by {request.delta}.",
            "updated_identity": updated
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
