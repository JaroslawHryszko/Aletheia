from fastapi import APIRouter, HTTPException
from aletheia.core import memory

router = APIRouter()

@router.get("/")
def get_latest_monologue():
    try:
        thoughts = memory.load_thoughts()
        monologues = [
            t for t in reversed(thoughts)
            if t.get("meta", {}).get("origin") == "monologue"
        ]
        if not monologues:
            raise HTTPException(status_code=404, detail="No monologues found.")
        return monologues[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
