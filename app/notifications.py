import logging

from maxapi import Bot

from app.config import settings

logger = logging.getLogger(__name__)

ACCESS_ACTIVATED_TEXT = (
    "Доступ к боту активирован. Пришлите xlsx-файл — верну его обратно."
)

_bot: Bot | None = None


def _get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(settings.max_bot_token)
    return _bot


async def notify_access_activated(max_user_id: int) -> None:
    try:
        await _get_bot().send_message(user_id=max_user_id, text=ACCESS_ACTIVATED_TEXT)
    except Exception:
        logger.exception(
            "Не удалось отправить уведомление об активации доступа max_user_id=%s",
            max_user_id,
        )


async def close_notifier() -> None:
    global _bot
    if _bot is not None:
        await _bot.close_session()
        _bot = None
