"""Точка входа для сервиса `migrate` в docker-compose.

Перед накатом миграций проверяет: если таблица max_users уже существует,
а alembic_version — нет, значит БД создана старым способом (create_all,
до перехода на Alembic). В этом случае сначала помечаем схему как
соответствующую базовой миграции, чтобы Alembic не пытался создать
уже существующую таблицу заново.
"""

import asyncio

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db import engine

BASELINE_REVISION = "98bd89a04d51"


async def _created_before_alembic() -> bool:
    async with engine.connect() as conn:
        def _check(sync_conn):
            tables = inspect(sync_conn).get_table_names()
            return "max_users" in tables and "alembic_version" not in tables

        return await conn.run_sync(_check)


def main() -> None:
    config = Config("alembic.ini")
    if asyncio.run(_created_before_alembic()):
        command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
