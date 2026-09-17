from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine: AsyncEngine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_models() -> None:
    """Создаёт таблицы, если их ещё нет. Без миграций: для добавления/
    изменения колонок в будущем таблицу пересоздают или правят вручную.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
