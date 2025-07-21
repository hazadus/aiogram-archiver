import os
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, Message
from loguru import logger
from services import (
    clear_user_files,
    create_user_archive,
    create_user_archive_by_date,
    format_file_size,
    get_user_files_stats,
    save_user_files,
)

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
    Обработчик команды /archive и /archive YYYY-MM-DD.

    Создаёт zip-архив со всеми файлами пользователя или с файлами за указанную дату.
    """
    if message.from_user is None:
        logger.error("Получено сообщение без данных пользователя")
        return

    user_id = message.from_user.id
    username = (
        message.from_user.username or message.from_user.first_name or "Пользователь"
    )

    # Извлекаем дату из команды, если она есть
    if message.text is None:
        logger.error("Получено сообщение без текста")
        return

    command_text = message.text.strip()
    parts = command_text.split()

    if len(parts) == 2:
        # Команда с датой: /archive YYYY-MM-DD
        target_date = parts[1]

        # Проверяем формат даты
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты. Используйте формат YYYY-MM-DD (например: 2024-01-15)"
            )
            return

        logger.debug(
            f"Получена команда /archive {target_date} от пользователя {user_id} (@{username})"
        )

        # Отправляем сообщение о начале создания архива
        status_message = await message.answer(
            f"📦 Создаю архив с файлами за {target_date}..."
        )

        try:
            # Создаём архив за указанную дату
            archive_path = await create_user_archive_by_date(
                user_id=user_id,
                target_date=target_date,
            )

            if archive_path is None:
                await status_message.edit_text(
                    f"📁 У вас нет сохранённых файлов за {target_date}."
                )
                return

            # Читаем архив и отправляем его пользователю
            archive_file = Path(archive_path)
            with open(archive_file, "rb") as file:
                archive_data = file.read()

            # Создаём имя файла для архива
            archive_filename = f"archive_{username}_{user_id}_{target_date}.zip"

            # Отправляем архив как документ
            document = BufferedInputFile(archive_data, filename=archive_filename)
            await bot.send_document(
                chat_id=message.chat.id,
                document=document,
                caption=f"📦 Ваш архив с файлами за {target_date} готов!",
            )

            # Удаляем сообщение о статусе
            await status_message.delete()

            logger.info(f"Архив за {target_date} отправлен пользователю {user_id}")

        except Exception as e:
            logger.error(
                f"Ошибка при отправке архива за {target_date} пользователю {user_id}: {e}"
            )
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

    else:
        # Обычная команда /archive без даты
        logger.debug(
            f"Получена команда /archive от пользователя {user_id} (@{username})"
        )

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
        "/stats - Показать статистику по сохранённым файлам\n"
        "/archive - Создать и получить zip-архив со всеми вашими файлами\n"
        "/archive YYYY-MM-DD - Создать архив только с файлами за указанную дату\n"
        "/clear - Удалить все ваши сохранённые файлы\n\n"
        "📁 **Работа с файлами:**\n"
        "• Отправьте любой файл, фото, видео, аудио, документ или стикер - бот автоматически сохранит его\n"
        "• Используйте /stats для просмотра статистики файлов\n"
        "• Используйте /archive для получения архива с вашими файлами\n"
        "• Используйте /archive YYYY-MM-DD для получения архива с файлами за конкретную дату\n"
        "• Используйте /clear для удаления всех сохранённых файлов"
    )

    await message.answer(help_text, parse_mode="Markdown")


# MARK: Stats
@router.message(Command("stats"))
async def stats_command_handler(message: Message) -> None:
    """
    Обработчик команды /stats.

    Отправляет пользователю статистику по сохраненным файлам.
    """
    if message.from_user is None:
        logger.error("Получено сообщение без данных пользователя")
        return

    user_id = message.from_user.id
    username = (
        message.from_user.username or message.from_user.first_name or "Пользователь"
    )

    logger.debug(f"Получена команда /stats от пользователя {user_id} (@{username})")

    # Получаем статистику файлов
    stats = get_user_files_stats(user_id=user_id)

    if stats["total_files"] == 0:
        await message.answer("📁 У вас нет сохранённых файлов.")
        return

    # Формируем общую статистику
    total_size_formatted = format_file_size(stats["total_size"])
    stats_text = (
        f"📊 **Статистика ваших файлов:**\n\n"
        f"📁 Всего файлов: {stats['total_files']}\n"
        f"💾 Общий объём: {total_size_formatted}\n\n"
        f"📅 **По датам:**\n"
    )

    # Добавляем статистику по датам
    for date, date_stats in stats["files_by_date"].items():
        date_size_formatted = format_file_size(date_stats["size"])
        stats_text += f"• {date}: {date_stats['count']} файлов, {date_size_formatted}\n"

    await message.answer(stats_text, parse_mode="Markdown")


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
