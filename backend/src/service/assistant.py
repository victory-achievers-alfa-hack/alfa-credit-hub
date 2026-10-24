from sqlalchemy.orm import Session

from backend.src.schemas import assistant as assistant_schemas


def chat_to_assistant(
    question: assistant_schemas.AssistantChatRequest, db: Session
) -> assistant_schemas.AssistantChatResponse:
    pass
