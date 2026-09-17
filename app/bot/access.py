import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MaxUser


def normalize_phone(raw: str) -> str:
    """Приводит номер к виду 7XXXXXXXXXX независимо от формата ввода."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    return digits


async def get_user_by_max_id(
    session: AsyncSession, max_user_id: int
) -> MaxUser | None:
    result = await session.execute(
        select(MaxUser).where(MaxUser.max_user_id == max_user_id)
    )
    return result.scalar_one_or_none()


async def link_phone_to_max_id(
    session: AsyncSession,
    phone: str,
    max_user_id: int,
    display_name: str | None,
) -> MaxUser:
    """Находит запись по номеру телефона и привязывает к ней max_user_id.

    Если записи с таким телефоном ещё нет (админ пока не добавил доступ),
    создаёт её без доступа — как только админ проставит номер и срок,
    привязка уже будет на месте.
    """
    normalized = normalize_phone(phone)
    result = await session.execute(
        select(MaxUser).where(MaxUser.phone == normalized)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = MaxUser(
            phone=normalized,
            max_user_id=max_user_id,
            display_name=display_name,
            is_active=False,
        )
        session.add(user)
    else:
        user.max_user_id = max_user_id
        if display_name:
            user.display_name = display_name

    await session.commit()
    await session.refresh(user)
    return user
