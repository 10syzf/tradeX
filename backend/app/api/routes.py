from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.models import AppSettingEntity, MessageEntity, SessionEntity
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.session import MessageRead, SessionCreateRequest, SessionDetail, SessionSummary
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.get('/health')
def health():
    settings = get_settings()
    return {
        'status': 'ok',
        'app_name': settings.app_name,
        'version': settings.app_version,
        'llm_provider': settings.llm_provider,
        'llm_model': settings.active_model,
    }


@router.post('/sessions', response_model=SessionSummary)
def create_session(payload: SessionCreateRequest, db: Session = Depends(get_db)):
    now = _now()
    session = SessionEntity(
        id=str(uuid4()),
        title=payload.title or '新会话',
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    _ensure_default_settings(db)
    return SessionSummary.model_validate(session, from_attributes=True)


@router.get('/sessions', response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.scalars(select(SessionEntity).order_by(SessionEntity.updated_at.desc())).all()
    return [SessionSummary.model_validate(item, from_attributes=True) for item in sessions]


@router.get('/sessions/{session_id}/messages', response_model=SessionDetail)
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    session = db.get(SessionEntity, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail='会话不存在')

    messages = [MessageRead.model_validate(item, from_attributes=True) for item in session.messages]
    return SessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages,
    )


@router.post('/chat', response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = await chat_service.send_message(db, payload.session_id, payload.message, payload.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatResponse(**result)


@router.get('/settings')
def get_settings_snapshot(db: Session = Depends(get_db)):
    settings = get_settings()
    setting = _ensure_default_settings(db)
    return {
        'llm_provider': settings.llm_provider,
        'default_model': setting.default_model,
        'temperature': setting.temperature,
        'max_context_messages': setting.max_context_messages,
        'agent_max_steps': settings.agent_max_steps,
        'agent_log_level': settings.agent_log_level,
    }


@router.get('/stock-tool/status')
def get_stock_tool_status():
    return {
        'status': 'not_connected',
        'message': '股票工具预留完成，真实行情源将在下一阶段接入。',
    }



def _ensure_default_settings(db: Session) -> AppSettingEntity:
    settings = get_settings()
    setting = db.scalar(select(AppSettingEntity).limit(1))
    if setting is not None:
        changed = False
        if setting.default_model != settings.active_model:
            setting.default_model = settings.active_model
            changed = True
        if setting.max_context_messages != settings.max_context_messages:
            setting.max_context_messages = settings.max_context_messages
            changed = True
        if changed:
            setting.updated_at = _now()
            db.commit()
            db.refresh(setting)
        return setting

    now = _now()
    setting = AppSettingEntity(
        default_model=settings.active_model,
        temperature='0.7',
        max_context_messages=settings.max_context_messages,
        created_at=now,
        updated_at=now,
    )
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting



def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
