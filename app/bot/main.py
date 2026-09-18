import asyncio
import logging

from maxapi import Bot

from app.bot.handlers import dp
from app.config import settings
from app.db import init_models
from app.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    await init_models()
    bot = Bot(settings.max_bot_token)
    start_scheduler()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
