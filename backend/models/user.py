import datetime
from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    openid: Mapped[str] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    conversations: Mapped[list["ConversationModel"]] = relationship(back_populates="user")
