# aletheia/api/routes/telegram_webhook.py
from fastapi import APIRouter, Request, HTTPException, Depends
from aletheia.core.initiator import ConversationInitiator

router = APIRouter()
initiator = ConversationInitiator()

@router.post("/")
async def telegram_webhook(request: Request):
    try:
        update_data = await request.body()
        initiator.handle_telegram_update(update_data)
        return {"status": "processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))