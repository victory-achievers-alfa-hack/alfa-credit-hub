from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import assistant as assistant_service


router = APIRouter()


@router.post("/assistant/chat")
def chat_to_assistant(user_id: int, db: Session = Depends(get_db)) -> dict:
    return assistant_service.chat_to_assistant(user_id, db)