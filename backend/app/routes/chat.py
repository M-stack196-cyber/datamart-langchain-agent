from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.chat_service import process_chat
from app.db.session import get_db
from app.schemas import ChatRequest, ChatResponse


router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        response, conversation_id = process_chat(
            db=db,
            message=payload.message.strip(),
            conversation_id=payload.conversation_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    return ChatResponse(response=response, conversation_id=conversation_id)
