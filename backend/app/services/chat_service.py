from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.adapters.llm import LLMAdapter
from app.core.config import get_settings
from app.models import MessageEntity, SessionEntity
from app.services.memory import MemoryService
from app.services.stock_tool import StockToolService


class ChatService:
    def __init__(self):
        self.settings = get_settings()
        self.memory_service = MemoryService()
        self.stock_tool = StockToolService()
        self.llm = LLMAdapter(self.settings)

    async def send_message(self, db: Session, session_id: str, user_message: str, model: str | None):
        session = db.get(SessionEntity, session_id)
        if session is None:
            raise ValueError('会话不存在')

        now = self._now()
        user_record = MessageEntity(
            id=str(uuid4()),
            session_id=session_id,
            role='user',
            content=user_message,
            created_at=now,
        )
        db.add(user_record)
        db.flush()

        all_messages = list(session.messages) + [user_record]
        context = self.memory_service.build_context(all_messages, self.settings.max_context_messages)
        reply, llm_warnings = await self.llm.generate_reply(context, model)

        assistant_record = MessageEntity(
            id=str(uuid4()),
            session_id=session_id,
            role='assistant',
            content=reply,
            created_at=self._now(),
        )
        db.add(assistant_record)
        session.updated_at = self._now()
        db.commit()

        stock_status = self.stock_tool.get_status()
        warnings = llm_warnings[:]
        if stock_status['status'] != 'connected':
            warnings.append(stock_status['message'])

        return {
            'session_id': session_id,
            'reply': reply,
            'tool_calls': [],
            'warnings': warnings,
        }

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
