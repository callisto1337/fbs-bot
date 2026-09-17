import logging

from maxapi import Dispatcher
from maxapi.filters import Contact as ContactFilter
from maxapi.types import CommandStart, InputMediaBuffer, MessageCreated, RequestContactButton
from maxapi.types.attachments import Contact as ContactAttachment
from maxapi.types.attachments import File
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from app.bot.access import get_user_by_max_id, link_phone_to_max_id
from app.db import async_session
from app.xlsx_processing import process_xlsx

logger = logging.getLogger(__name__)

dp = Dispatcher()

CONTACT_PROMPT = (
    "Чтобы пользоваться ботом, поделитесь номером телефона, "
    "на который оформлена оплата доступа."
)


def _contact_keyboard() -> list:
    builder = InlineKeyboardBuilder()
    builder.row(RequestContactButton(text="Поделиться номером"))
    return [builder.as_markup()]


async def _request_contact(event: MessageCreated) -> None:
    await event.message.answer(CONTACT_PROMPT, attachments=_contact_keyboard())


# Порядок регистрации handler'ов важен: диспетчер вызывает первый, чей
# фильтр совпал, поэтому более специфичные обработчики (команда, контакт)
# идут раньше "общего" on_message.


@dp.message_created(CommandStart())
async def on_start(event: MessageCreated) -> None:
    _, user_id = event.get_ids()
    user = None
    if user_id is not None:
        async with async_session() as session:
            user = await get_user_by_max_id(session, user_id)

    if user is not None and user.has_access():
        await event.message.answer(
            "Доступ есть. Пришлите xlsx-файл — верну его обратно."
        )
        return

    await _request_contact(event)


@dp.message_created(ContactFilter())
async def on_contact(event: MessageCreated, contact: ContactAttachment) -> None:
    _, user_id = event.get_ids()
    if user_id is None or contact.payload is None:
        await event.message.answer(
            "Не удалось определить пользователя, попробуйте ещё раз."
        )
        return

    phone = contact.payload.vcf.phone
    if not phone:
        await event.message.answer(
            "Не удалось прочитать номер телефона из контакта, попробуйте ещё раз."
        )
        return

    display_name = (
        contact.payload.max_info.full_name if contact.payload.max_info else None
    )

    async with async_session() as session:
        user = await link_phone_to_max_id(session, phone, user_id, display_name)

    if user.has_access():
        await event.message.answer(
            "Номер подтверждён, доступ активен. Пришлите xlsx-файл."
        )
    else:
        await event.message.answer(
            "Номер сохранён. Доступ откроется, как только администратор его активирует."
        )


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
        await event.message.answer("Пришлите файл в формате .xlsx.")
        return

    filename = file_attachment.filename or "result.xlsx"
    if not filename.lower().endswith(".xlsx"):
        await event.message.answer("Поддерживаются только файлы .xlsx.")
        return

    if file_attachment.payload is None:
        await event.message.answer("Не удалось получить файл, попробуйте ещё раз.")
        return

    data = await event.bot.download_bytes(url=file_attachment.payload.url)
    result = process_xlsx(data)

    await event.message.answer(
        "Готово, ваш файл обработан:",
        attachments=[InputMediaBuffer(buffer=result, filename=filename)],
    )
