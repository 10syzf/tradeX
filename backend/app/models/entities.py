from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SessionEntity(Base):
    __tablename__ = 'sessions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(32), nullable=False)

    messages: Mapped[list['MessageEntity']] = relationship(
        back_populates='session',
        cascade='all, delete-orphan',
        order_by='MessageEntity.created_at',
    )


class MessageEntity(Base):
    __tablename__ = 'messages'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('sessions.id'), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)

    session: Mapped['SessionEntity'] = relationship(back_populates='messages')


class AppSettingEntity(Base):
    __tablename__ = 'app_settings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    default_model: Mapped[str] = mapped_column(String(128), nullable=False)
    temperature: Mapped[str] = mapped_column(String(16), nullable=False, default='0.7')
    max_context_messages: Mapped[int] = mapped_column(nullable=False, default=12)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(32), nullable=False)
