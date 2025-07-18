import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from config import settings
from loguru import logger

dp = Dispatcher()


@dp.message()
async def message_handler(message: Message) -> None:
    chat_id = message.chat.id
    message_str = message.text

    if message_str is None:
        return

    # Определим, как обращаться к пользователю
    from_user = message.from_user
    if from_user is not None:
        username = from_user.username or from_user.first_name or "чувак"
    else:
        username = "чувак"

    answer = f"{username} ({chat_id=}): {message_str}"
    logger.debug(answer)
    await message.answer(answer)


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
