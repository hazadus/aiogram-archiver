import os
from pathlib import Path

from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, Message
from loguru import logger
from services import clear_user_files, create_user_archive, save_user_files

router = Router()


# MARK: Start
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
        "• Создавать и отправлять вам zip-архив с вашими файлами\n"
        "• Удалять все ваши файлы командой /clear\n\n"
        "Используйте /help для получения списка всех команд."
    )

    await message.answer(
        welcome_text,
    )


# MARK: Archive
@router.message(Command("archive"))
async def archive_command_handler(message: Message, bot: Bot) -> None:
    """
    Обработчик команды /archive.

    Создаёт zip-архив со всеми файлами пользователя и отправляет его.
    """
    if message.from_user is None:
        logger.error("Получено сообщение без данных пользователя")
        return

    user_id = message.from_user.id
    username = (
        message.from_user.username or message.from_user.first_name or "Пользователь"
    )

    logger.debug(f"Получена команда /archive от пользователя {user_id} (@{username})")

    # Отправляем сообщение о начале создания архива
    status_message = await message.answer("📦 Создаю архив с вашими файлами...")

    try:
        # Создаём архив
        archive_path = await create_user_archive(user_id)

        if archive_path is None:
            await status_message.edit_text(
                "📁 У вас нет сохранённых файлов для создания архива."
            )
            return

        # Читаем архив и отправляем его пользователю
        archive_file = Path(archive_path)
        with open(archive_file, "rb") as file:
            archive_data = file.read()

        # Создаём имя файла для архива
        archive_filename = f"archive_{username}_{user_id}.zip"

        # Отправляем архив как документ
        document = BufferedInputFile(archive_data, filename=archive_filename)
        await bot.send_document(
            chat_id=message.chat.id,
            document=document,
            caption="📦 Ваш архив с сохранёнными файлами готов!",
        )

        # Удаляем сообщение о статусе
        await status_message.delete()

        logger.info(f"Архив отправлен пользователю {user_id}")

    except Exception as e:
        logger.error(f"Ошибка при отправке архива пользователю {user_id}: {e}")
        await status_message.edit_text(
            "❌ Произошла ошибка при создании архива. Попробуйте позже."
        )
    finally:
        # Удаляем временный файл архива, если он существует
        if "archive_path" in locals() and archive_path:
            try:
                os.unlink(archive_path)
                logger.debug(f"Удалён временный архив {archive_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного архива: {e}")


# MARK: Clear
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


# MARK: Help
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
        "/archive - Создать и получить zip-архив со всеми вашими файлами\n"
        "/clear - Удалить все ваши сохранённые файлы\n\n"
        "📁 **Работа с файлами:**\n"
        "• Отправьте любой файл, фото, видео, аудио, документ или стикер - бот автоматически сохранит его\n"
        "• Используйте /archive для получения архива с вашими файлами\n"
        "• Используйте /clear для удаления всех сохранённых файлов"
    )

    await message.answer(help_text, parse_mode="Markdown")


# MARK: Any Message
# Должно быть после остальных обработчиков команд, чтобы не перехватывать команды
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
    saved_files = await save_user_files(message=message, bot=bot)

    if saved_files:
        files_count = len(saved_files)
        logger.info(f"Сохранено {files_count} файлов для пользователя {user_id}")
