from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from loguru import logger
from services import clear_user_files, save_user_files

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
        "• Удалять все ваши файлы командой /clear\n\n"
        "Используйте /help для получения списка всех команд."
    )

    await message.answer(
        welcome_text,
    )


@router.message(Command("clear"))
async def clear_command_handler(message: Message) -> None:
    """
    Обработчик команды /clear.

    Удаляет все файлы пользователя и сообщает количество удаленных файлов.
    """
    if message.from_user is None:
        logger.error("Получено сообщение без данных пользователя")
        return

    user_id = message.from_user.id
    username = (
        message.from_user.username or message.from_user.first_name or "Пользователь"
    )

    logger.debug(f"Получена команда /clear от пользователя {user_id} (@{username})")

    deleted_count = await clear_user_files(user_id)

    if deleted_count > 0:
        response_text = f"🗑️ Удалено файлов: {deleted_count}"
    else:
        response_text = "📁 У вас нет сохраненных файлов для удаления."

    await message.answer(response_text)


@router.message(Command("help"))
async def help_command_handler(message: Message) -> None:
    """
    Обработчик команды /help.

    Отправляет пользователю список доступных команд с их описанием.
    """
    if message.from_user is None:
        logger.error("Получено сообщение без данных пользователя")
        return

    user_id = message.from_user.id
    username = (
        message.from_user.username or message.from_user.first_name or "Пользователь"
    )

    logger.debug(f"Получена команда /help от пользователя {user_id} (@{username})")

    help_text = (
        "📋 **Доступные команды:**\n\n"
        "/start - Запустить бота и получить приветствие\n"
        "/help - Показать это сообщение с описанием команд\n"
        "/clear - Удалить все ваши сохранённые файлы\n\n"
        "📁 **Работа с файлами:**\n"
        "• Отправьте любой файл, фото, видео, аудио, документ или стикер - бот автоматически сохранит его\n"
        "• Используйте /clear для удаления всех сохранённых файлов\n"
        "• В будущем будет добавлена возможность получения архива с вашими файлами"
    )

    await message.answer(help_text, parse_mode="Markdown")


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
