import asyncio

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings
from handlers import router
from loguru import logger

if settings.SENTRY_DSN:
    # Инициализация Sentry/Bugsink для отслеживания ошибок
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        send_default_pii=True,
        max_request_body_size="always",
        traces_sample_rate=0,
    )

dp = Dispatcher()
dp.include_router(router)


async def main() -> None:
    logger.debug("Using token: {}", settings.TELEGRAM_BOT_TOKEN)
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    logger.info("🚀 Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
