from pydantic import BaseModel, Field, field_validator


class AssistantChatRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Почему не одобрили 800 тысяч?"], max_length=511)

    @field_validator("question")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field can't be empty")
        return v


class AssistantChatResponse(BaseModel):
    answer: str

    @field_validator("answer")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field can't be empty")
        return v