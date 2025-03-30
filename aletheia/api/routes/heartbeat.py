from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
def heartbeat():
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
