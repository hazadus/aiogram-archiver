from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger
from services import save_user_files

router = Router()


@router.message(CommandStart())
async def start_command_handler(message: Message) -> None:
    """
    Обработчик команды /start.

    Отправляет приветственное сообщение пользователю с информацией о доступных командах.
    """
    if message.from_user is None:
        logger.error("Получено сообщение без данных пользователя")
        return

    user_id = message.from_user.id
    username = (
        message.from_user.username or message.from_user.first_name or "Пользователь"
    )

    logger.debug(f"Получена команда /start от пользователя {user_id} (@{username})")

    welcome_text = (
        f"👋 Привет, {username}!\n\n"
        "Этот бот умеет следующее:\n"
        "• Сохранять полученные от вас файлы и изображения\n"
        "• Отправлять вам ваши файлы в архиве по запросу\n"
    )

    await message.answer(
        welcome_text,
    )


@router.message()
async def message_handler(message: Message, bot: Bot) -> None:
    """
    Обработчик всех остальных сообщений.

    Сохраняет файлы и изображения, если они есть, и отвечает пользователю.
    """
    if message.from_user is None:
        logger.error("Получено сообщение без данных пользователя")
        return

    user_id = message.from_user.id
    username = (
        message.from_user.username or message.from_user.first_name or "Пользователь"
    )

    logger.debug(f"Получено сообщение от пользователя {user_id} (@{username})")

    # Сохраняем файлы, если они есть в сообщении
    saved_files = await save_user_files(message, bot)

    if saved_files:
        files_count = len(saved_files)
        response_text = f"✅ Сохранено файлов: {files_count}"
        logger.info(f"Сохранено {files_count} файлов для пользователя {user_id}")
    else:
        response_text = "📝 Сообщение получено, но файлов для сохранения не найдено."

    await message.answer(response_text)
