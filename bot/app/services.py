import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from aiogram.types import (
    Audio,
    Document,
    Message,
    PhotoSize,
    Sticker,
    Video,
    VideoNote,
    Voice,
)
from config import settings
from loguru import logger


async def save_user_files(
    *,
    message: Message,
    bot: Bot,
) -> list[str]:
    """
    Сохраняет все файлы и изображения из сообщения пользователя на диск.

    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота для скачивания файлов

    Returns:
        Список путей к сохраненным файлам
    """
    if not message.from_user:
        logger.error("Получено сообщение без данных пользователя")
        return []

    user_id = message.from_user.id
    user_dir = Path(settings.FILES_DIR) / str(user_id)

    # Создаем директорию пользователя, если её нет
    user_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []

    # Обработка документов
    if message.document:
        file_path = await _save_document(
            document=message.document, user_dir=user_dir, bot=bot
        )
        if file_path:
            saved_files.append(file_path)

    # Обработка изображений
    if message.photo:
        file_path = await _save_photo(photos=message.photo, user_dir=user_dir, bot=bot)
        if file_path:
            saved_files.append(file_path)

    # Обработка аудио
    if message.audio:
        file_path = await _save_audio(audio=message.audio, user_dir=user_dir, bot=bot)
        if file_path:
            saved_files.append(file_path)

    # Обработка видео
    if message.video:
        file_path = await _save_video(video=message.video, user_dir=user_dir, bot=bot)
        if file_path:
            saved_files.append(file_path)

    # Обработка голосовых сообщений
    if message.voice:
        file_path = await _save_voice(voice=message.voice, user_dir=user_dir, bot=bot)
        if file_path:
            saved_files.append(file_path)

    # Обработка видеозаметок
    if message.video_note:
        file_path = await _save_video_note(
            video_note=message.video_note, user_dir=user_dir, bot=bot
        )
        if file_path:
            saved_files.append(file_path)

    # Обработка стикеров
    if message.sticker:
        file_path = await _save_sticker(
            sticker=message.sticker, user_dir=user_dir, bot=bot
        )
        if file_path:
            saved_files.append(file_path)

    if saved_files:
        logger.info(f"Сохранено {len(saved_files)} файлов для пользователя {user_id}")

    return saved_files


async def clear_user_files(user_id: int) -> int:
    """
    Удаляет все файлы пользователя.

    Args:
        user_id: ID пользователя

    Returns:
        Количество удаленных файлов
    """
    user_dir = Path(settings.FILES_DIR) / str(user_id)

    if not user_dir.exists():
        logger.debug(f"Директория пользователя {user_id} не существует")
        return 0

    try:
        # Подсчитываем количество файлов перед удалением
        files_count = sum(1 for file in user_dir.rglob("*") if file.is_file())

        # Удаляем всю директорию пользователя
        shutil.rmtree(user_dir)

        logger.info(f"Удалено {files_count} файлов для пользователя {user_id}")
        return files_count

    except Exception as e:
        logger.error(f"Ошибка при удалении файлов пользователя {user_id}: {e}")
        return 0


async def _save_document(
    *,
    document: Document,
    user_dir: Path,
    bot: Bot,
) -> str | None:
    """Сохраняет документ."""
    try:
        file = await bot.get_file(document.file_id)
        if not file.file_path:
            logger.error(f"Не удалось получить путь к файлу {document.file_id}")
            return None

        # Используем оригинальное имя файла или генерируем по file_id
        filename = document.file_name or f"{document.file_id}.bin"
        file_path = user_dir / filename

        # Если файл с таким именем уже существует, добавляем суффикс
        counter = 1
        original_path = file_path
        while file_path.exists():
            name = original_path.stem
            suffix = original_path.suffix
            file_path = user_dir / f"{name}_{counter}{suffix}"
            counter += 1

        await bot.download_file(file.file_path, file_path)
        logger.debug(f"Сохранён документ: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Ошибка при сохранении документа: {e}")
        return None


async def _save_photo(
    *,
    photos: list[PhotoSize],
    user_dir: Path,
    bot: Bot,
) -> str | None:
    """Сохраняет фото (выбирает максимальное разрешение)."""
    try:
        # Выбираем фото с максимальным разрешением
        photo = max(photos, key=lambda p: p.width * p.height)

        file = await bot.get_file(photo.file_id)
        if not file.file_path:
            logger.error(f"Не удалось получить путь к фото {photo.file_id}")
            return None

        # Определяем расширение по пути файла или используем .jpg по умолчанию
        extension = Path(file.file_path).suffix or ".jpg"
        filename = f"{photo.file_id}{extension}"
        file_path = user_dir / filename

        # Если файл уже существует, добавляем суффикс
        counter = 1
        original_path = file_path
        while file_path.exists():
            name = original_path.stem
            suffix = original_path.suffix
            file_path = user_dir / f"{name}_{counter}{suffix}"
            counter += 1

        await bot.download_file(file.file_path, file_path)
        logger.debug(f"Сохранено фото: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Ошибка при сохранении фото: {e}")
        return None


async def _save_audio(
    *,
    audio: Audio,
    user_dir: Path,
    bot: Bot,
) -> str | None:
    """Сохраняет аудио файл."""
    try:
        file = await bot.get_file(audio.file_id)
        if not file.file_path:
            logger.error(f"Не удалось получить путь к аудио {audio.file_id}")
            return None

        # Используем оригинальное имя или генерируем
        filename = audio.file_name or f"{audio.file_id}.mp3"
        file_path = user_dir / filename

        counter = 1
        original_path = file_path
        while file_path.exists():
            name = original_path.stem
            suffix = original_path.suffix
            file_path = user_dir / f"{name}_{counter}{suffix}"
            counter += 1

        await bot.download_file(file.file_path, file_path)
        logger.debug(f"Сохранено аудио: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Ошибка при сохранении аудио: {e}")
        return None


async def _save_video(
    *,
    video: Video,
    user_dir: Path,
    bot: Bot,
) -> str | None:
    """Сохраняет видео файл."""
    try:
        file = await bot.get_file(video.file_id)
        if not file.file_path:
            logger.error(f"Не удалось получить путь к видео {video.file_id}")
            return None

        filename = video.file_name or f"{video.file_id}.mp4"
        file_path = user_dir / filename

        counter = 1
        original_path = file_path
        while file_path.exists():
            name = original_path.stem
            suffix = original_path.suffix
            file_path = user_dir / f"{name}_{counter}{suffix}"
            counter += 1

        await bot.download_file(file.file_path, file_path)
        logger.debug(f"Сохранено видео: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Ошибка при сохранении видео: {e}")
        return None


async def _save_voice(
    *,
    voice: Voice,
    user_dir: Path,
    bot: Bot,
) -> str | None:
    """Сохраняет голосовое сообщение."""
    try:
        file = await bot.get_file(voice.file_id)
        if not file.file_path:
            logger.error(
                f"Не удалось получить путь к голосовому сообщению {voice.file_id}"
            )
            return None

        filename = f"{voice.file_id}.ogg"
        file_path = user_dir / filename

        counter = 1
        original_path = file_path
        while file_path.exists():
            name = original_path.stem
            suffix = original_path.suffix
            file_path = user_dir / f"{name}_{counter}{suffix}"
            counter += 1

        await bot.download_file(file.file_path, file_path)
        logger.debug(f"Сохранено голосовое сообщение: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Ошибка при сохранении голосового сообщения: {e}")
        return None


async def _save_video_note(
    *,
    video_note: VideoNote,
    user_dir: Path,
    bot: Bot,
) -> str | None:
    """Сохраняет видеозаметку."""
    try:
        file = await bot.get_file(video_note.file_id)
        if not file.file_path:
            logger.error(
                f"Не удалось получить путь к видеозаметке {video_note.file_id}"
            )
            return None

        filename = f"{video_note.file_id}.mp4"
        file_path = user_dir / filename

        counter = 1
        original_path = file_path
        while file_path.exists():
            name = original_path.stem
            suffix = original_path.suffix
            file_path = user_dir / f"{name}_{counter}{suffix}"
            counter += 1

        await bot.download_file(file.file_path, file_path)
        logger.debug(f"Сохранена видеозаметка: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Ошибка при сохранении видеозаметки: {e}")
        return None


async def _save_sticker(
    *,
    sticker: Sticker,
    user_dir: Path,
    bot: Bot,
) -> str | None:
    """Сохраняет стикер."""
    try:
        file = await bot.get_file(sticker.file_id)
        if not file.file_path:
            logger.error(f"Не удалось получить путь к стикеру {sticker.file_id}")
            return None

        # Определяем расширение: .webp для обычных стикеров, .tgs для анимированных
        extension = ".tgs" if sticker.is_animated else ".webp"
        filename = f"{sticker.file_id}{extension}"
        file_path = user_dir / filename

        counter = 1
        original_path = file_path
        while file_path.exists():
            name = original_path.stem
            suffix = original_path.suffix
            file_path = user_dir / f"{name}_{counter}{suffix}"
            counter += 1

        await bot.download_file(file.file_path, file_path)
        logger.debug(f"Сохранён стикер: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Ошибка при сохранении стикера: {e}")
        return None


async def create_user_archive(user_id: int) -> str | None:
    """
    Создаёт zip-архив со всеми файлами пользователя.

    Args:
        user_id: ID пользователя

    Returns:
        Путь к созданному архиву или None, если файлов нет или произошла ошибка
    """
    user_dir = Path(settings.FILES_DIR) / str(user_id)

    if not user_dir.exists():
        logger.debug(f"Директория пользователя {user_id} не существует")
        return None

    # Находим все файлы пользователя
    user_files = list(user_dir.rglob("*"))
    user_files = [f for f in user_files if f.is_file()]

    if not user_files:
        logger.debug(f"У пользователя {user_id} нет сохранённых файлов")
        return None

    try:
        # Создаём временный файл для архива
        temp_archive = tempfile.NamedTemporaryFile(
            delete=False, suffix=".zip", prefix=f"user_{user_id}_"
        )
        archive_path = temp_archive.name
        temp_archive.close()

        # Создаём zip-архив
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in user_files:
                # Добавляем файл в архив с относительным путём
                arcname = file_path.relative_to(user_dir)
                zip_file.write(file_path, arcname)

        logger.info(
            f"Создан архив {archive_path} с {len(user_files)} файлами для пользователя {user_id}"
        )
        return archive_path

    except Exception as e:
        logger.error(f"Ошибка при создании архива для пользователя {user_id}: {e}")
        return None


def get_user_files_stats(
    *,
    user_id: int,
) -> dict:
    """
    Получает статистику файлов пользователя.

    Args:
        user_id: ID пользователя

    Returns:
        Словарь со статистикой файлов
    """
    user_dir = Path(settings.FILES_DIR) / str(user_id)

    if not user_dir.exists():
        logger.debug(f"Директория пользователя {user_id} не существует")
        return {
            "total_files": 0,
            "total_size": 0,
            "files_by_date": {},
        }

    try:
        # Находим все файлы пользователя
        user_files = list(user_dir.rglob("*"))
        user_files = [f for f in user_files if f.is_file()]

        if not user_files:
            logger.debug(f"У пользователя {user_id} нет сохранённых файлов")
            return {
                "total_files": 0,
                "total_size": 0,
                "files_by_date": {},
            }

        total_size = 0
        files_by_date = {}

        for file_path in user_files:
            try:
                # Получаем размер файла
                file_size = file_path.stat().st_size
                total_size += file_size

                # Получаем дату создания файла
                file_ctime = datetime.fromtimestamp(file_path.stat().st_ctime)
                date_key = file_ctime.strftime("%Y-%m-%d")

                if date_key not in files_by_date:
                    files_by_date[date_key] = {"count": 0, "size": 0}

                files_by_date[date_key]["count"] += 1
                files_by_date[date_key]["size"] += file_size

            except Exception as e:
                logger.error(f"Ошибка при обработке файла {file_path}: {e}")
                continue

        # Сортируем даты по убыванию
        files_by_date = dict(sorted(files_by_date.items(), reverse=True))

        stats = {
            "total_files": len(user_files),
            "total_size": total_size,
            "files_by_date": files_by_date,
        }

        logger.debug(f"Получена статистика для пользователя {user_id}: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Ошибка при получении статистики для пользователя {user_id}: {e}")
        return {
            "total_files": 0,
            "total_size": 0,
            "files_by_date": {},
        }


def format_file_size(size_bytes: int) -> str:
    """
    Форматирует размер файла в читаемый вид.

    Args:
        size_bytes: Размер в байтах

    Returns:
        Отформатированный размер (например, "1.5 Мб", "2.3 Гб")
    """
    if size_bytes == 0:
        return "0 Б"

    # Константы для конвертации
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024

    if size_bytes < KB:
        return f"{size_bytes} Б"
    elif size_bytes < MB:
        return f"{size_bytes / KB:.1f} Кб"
    elif size_bytes < GB:
        return f"{size_bytes / MB:.1f} Мб"
    else:
        return f"{size_bytes / GB:.1f} Гб"
