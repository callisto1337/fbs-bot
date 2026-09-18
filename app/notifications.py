import logging

from maxapi import Bot

from app.config import settings

logger = logging.getLogger(__name__)

ACCESS_ACTIVATED_TEXT = (
    "Доступ к боту активирован. Пришлите xlsx-файл — верну его обратно."
)
ACCESS_REVOKED_TEXT = (
    "Доступ к боту приостановлен. Если это неожиданно, свяжитесь с администратором."
)
ACCESS_EXPIRED_TEXT = (
    "Срок действия доступа к боту истёк. Чтобы продолжить пользоваться ботом, "
    "обратитесь к администратору для продления."
)

_bot: Bot | None = None


def _get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(settings.max_bot_token)
    return _bot


async def _send(max_user_id: int, text: str) -> None:
    try:
        await _get_bot().send_message(user_id=max_user_id, text=text)
    except Exception:
        logger.exception(
            "Не удалось отправить уведомление max_user_id=%s", max_user_id
        )


async def notify_access_activated(max_user_id: int) -> None:
    await _send(max_user_id, ACCESS_ACTIVATED_TEXT)


async def notify_access_revoked(max_user_id: int) -> None:
    await _send(max_user_id, ACCESS_REVOKED_TEXT)


async def notify_access_expired(max_user_id: int) -> None:
    await _send(max_user_id, ACCESS_EXPIRED_TEXT)


async def close_notifier() -> None:
    global _bot
    if _bot is not None:
        await _bot.close_session()
        _bot = None
