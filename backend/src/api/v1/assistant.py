from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import assistant as assistant_service
from backend.src.schemas import assistant as assistant_schemas


router = APIRouter()


@router.post("/assistant/chat")
def chat_to_assistant(
        question: assistant_schemas.AssistantChatRequest,
        db: Session = Depends(get_db)
) -> assistant_schemas.AssistantChatResponse:
    return assistant_service.chat_to_assistant(question, db)