import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=True)
    character_id: Mapped[str] = mapped_column(String(32), default="sweet")
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["UserModel"] = relationship(back_populates="conversations")
    messages: Mapped[list["MessageModel"]] = relationship(back_populates="conversation")
