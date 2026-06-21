from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1)
    model: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: list[dict] = []
    warnings: list[str] = []
