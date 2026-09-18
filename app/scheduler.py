import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.db import async_session
from app.models import MaxUser
from app.notifications import notify_access_expired

logger = logging.getLogger(__name__)

CHECK_INTERVAL_MINUTES = 15


async def check_expired_access() -> None:
    """Находит пользователей, у которых access_expires_at уже наступил,
    но уведомление об этом ещё не отправлялось, и уведомляет их."""
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(
            select(MaxUser).where(
                MaxUser.is_active.is_(True),
                MaxUser.access_expires_at.is_not(None),
                MaxUser.access_expires_at <= now,
                MaxUser.expiry_notified_at.is_(None),
                MaxUser.max_user_id.is_not(None),
            )
        )
        expired_users = result.scalars().all()

        for user in expired_users:
            await notify_access_expired(user.max_user_id)
            user.expiry_notified_at = now

        if expired_users:
            await session.commit()
            logger.info("Отправлены уведомления об истечении доступа: %d", len(expired_users))


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_expired_access,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        id="check_expired_access",
    )
    scheduler.start()
    return scheduler
