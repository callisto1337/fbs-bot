from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MaxUser(Base):
    __tablename__ = "max_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Телефон, на который оформляется подписка. Заполняется админом вручную
    # и/или подтверждается пользователем через "Поделиться номером" в боте.
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    # ID пользователя в MAX. Заполняется автоматически, когда пользователь
    # подтвердил номер телефона в боте.
    max_user_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, index=True, nullable=True
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Пусто = бессрочный доступ.
    access_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Момент отправки уведомления об истечении access_expires_at. Пусто —
    # уведомление ещё не отправлено (или доступ с тех пор продлили).
    # Используется планировщиком, чтобы не слать уведомление повторно.
    expiry_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def has_access(self) -> bool:
        if not self.is_active:
            return False
        if self.access_expires_at is None:
            return True
        expires = self.access_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires > datetime.now(timezone.utc)
