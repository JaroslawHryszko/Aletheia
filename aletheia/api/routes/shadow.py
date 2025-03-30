from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pathlib import Path
import json

router = APIRouter()

SHADOW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "shadows"
SHADOW_DIR.mkdir(parents=True, exist_ok=True)

# === Request model ===

class ShadowEntry(BaseModel):
    content: str
    cause: Optional[str] = "unspecified"

# === Endpoints ===

@router.post("/")
def add_shadow(entry: ShadowEntry):
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d__%H%M%S")
        filename = f"shadow__{timestamp}.json"
        filepath = SHADOW_DIR / filename

        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "cause": entry.cause,
            "content": entry.content.strip()
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return {"message": "Shadow recorded.", "file": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_shadows():
    try:
        files = sorted(SHADOW_DIR.glob("shadow__*.json"))
        return [f.name for f in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{filename}")
def read_shadow(filename: str):
    try:
        filepath = SHADOW_DIR / filename
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Shadow not found.")
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
