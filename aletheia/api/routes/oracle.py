from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aletheia.core.oracle_client import ask_oracle

router = APIRouter()

# === Request/Response Schema ===

class OracleRequest(BaseModel):
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 300
    model: str = None

class OracleResponse(BaseModel):
    reply: str

# === Endpoint ===

@router.post("/", response_model=OracleResponse)
def query_oracle(request: OracleRequest):
    try:
        reply = ask_oracle(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model=request.model
        )
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
