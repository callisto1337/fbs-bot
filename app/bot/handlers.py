import logging

from maxapi import Dispatcher
from maxapi.filters import Contact as ContactFilter
from maxapi.types import (
    BotStarted,
    CommandStart,
    InputMediaBuffer,
    MessageCreated,
    RequestContactButton,
)
from maxapi.types.attachments import Contact as ContactAttachment
from maxapi.types.attachments import File
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from app.bot.access import get_user_by_max_id, link_phone_to_max_id
from app.db import async_session
from app.xlsx_processing import UnrecognizedReportFormatError, process_xlsx

logger = logging.getLogger(__name__)

dp = Dispatcher()

CONTACT_PROMPT = (
    "Чтобы пользоваться ботом, поделитесь номером телефона, "
    "на который оформлена оплата доступа."
)
SHARE_PHONE_BUTTON_TEXT = "Поделиться номером"
ACCESS_GRANTED_TEXT = "Доступ есть. Пришлите xlsx-файл — верну его обратно."
USER_NOT_IDENTIFIED_TEXT = "Не удалось определить пользователя, попробуйте ещё раз."
PHONE_NOT_READABLE_TEXT = (
    "Не удалось прочитать номер телефона из контакта, попробуйте ещё раз."
)
PHONE_CONFIRMED_ACCESS_TEXT = "Номер подтверждён, доступ активен. Пришлите xlsx-файл."
PHONE_CONFIRMED_NO_ACCESS_TEXT = (
    "Номер сохранён. Доступ откроется, как только администратор его активирует."
)
NO_FILE_ATTACHED_TEXT = "Пришлите файл в формате .xlsx."
WRONG_EXTENSION_TEXT = "Поддерживаются только файлы .xlsx."
FILE_DOWNLOAD_FAILED_TEXT = "Не удалось получить файл, попробуйте ещё раз."
FILE_PROCESSED_TEXT = "Готово, ваш файл обработан:"


def _contact_keyboard() -> list:
    builder = InlineKeyboardBuilder()
    builder.row(RequestContactButton(text=SHARE_PHONE_BUTTON_TEXT))
    return [builder.as_markup()]


async def _request_contact(event: BotStarted | MessageCreated) -> None:
    # event.send(...) — общий shortcut и для BotStarted, и для MessageCreated
    # (в отличие от event.message.answer, которого у BotStarted нет).
    await event.send(CONTACT_PROMPT, attachments=_contact_keyboard())


async def _greet_or_request_contact(event: BotStarted | MessageCreated) -> None:
    _, user_id = event.get_ids()
    user = None
    if user_id is not None:
        async with async_session() as session:
            user = await get_user_by_max_id(session, user_id)

    if user is not None and user.has_access():
        await event.send(ACCESS_GRANTED_TEXT)
        return

    await _request_contact(event)


# Порядок регистрации handler'ов важен: диспетчер вызывает первый, чей
# фильтр совпал, поэтому более специфичные обработчики (команда, контакт)
# идут раньше "общего" on_message.


@dp.bot_started()
async def on_bot_started(event: BotStarted) -> None:
    # Срабатывает при первом открытии чата с ботом — до того, как
    # пользователь что-либо написал.
    await _greet_or_request_contact(event)


@dp.message_created(CommandStart())
async def on_start(event: MessageCreated) -> None:
    await _greet_or_request_contact(event)


@dp.message_created(ContactFilter())
async def on_contact(event: MessageCreated, contact: ContactAttachment) -> None:
    _, user_id = event.get_ids()
    if user_id is None or contact.payload is None:
        await event.message.answer(USER_NOT_IDENTIFIED_TEXT)
        return

    phone = contact.payload.vcf.phone
    if not phone:
        await event.message.answer(PHONE_NOT_READABLE_TEXT)
        return

    display_name = (
        contact.payload.max_info.full_name if contact.payload.max_info else None
    )

    async with async_session() as session:
        user = await link_phone_to_max_id(session, phone, user_id, display_name)

    if user.has_access():
        await event.message.answer(PHONE_CONFIRMED_ACCESS_TEXT)
    else:
        await event.message.answer(PHONE_CONFIRMED_NO_ACCESS_TEXT)


@dp.message_created()
async def on_message(event: MessageCreated) -> None:
    body = event.message.body
    attachments = body.attachments if body and body.attachments else []
    file_attachment = next((a for a in attachments if isinstance(a, File)), None)

    _, user_id = event.get_ids()
    user = None
    if user_id is not None:
        async with async_session() as session:
            user = await get_user_by_max_id(session, user_id)

    if user is None or not user.has_access():
        await _request_contact(event)
        return

    if file_attachment is None:
        await event.message.answer(NO_FILE_ATTACHED_TEXT)
        return

    filename = file_attachment.filename or "result.xlsx"
    if not filename.lower().endswith(".xlsx"):
        await event.message.answer(WRONG_EXTENSION_TEXT)
        return

    if file_attachment.payload is None:
        await event.message.answer(FILE_DOWNLOAD_FAILED_TEXT)
        return

    data = await event.bot.download_bytes(url=file_attachment.payload.url)
    try:
        result = process_xlsx(data)
    except UnrecognizedReportFormatError as exc:
        await event.message.answer(str(exc))
        return

    await event.message.answer(
        FILE_PROCESSED_TEXT,
        attachments=[InputMediaBuffer(buffer=result, filename=filename)],
    )
