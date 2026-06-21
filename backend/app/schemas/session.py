from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    title: str = '新会话'


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageRead(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: str


class SessionDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageRead]
