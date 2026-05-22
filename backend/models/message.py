import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(32), ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    emotion: Mapped[str] = mapped_column(String(20), nullable=True)
    has_voice: Mapped[bool] = mapped_column(Boolean, default=False)
    voice_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped["ConversationModel"] = relationship(back_populates="messages")
