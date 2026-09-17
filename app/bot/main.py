import asyncio
import logging

from maxapi import Bot

from app.bot.handlers import dp
from app.config import settings

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(settings.max_bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
