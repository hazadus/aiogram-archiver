FROM python:3.12-slim

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Создаем и устанавливаем рабочую директорию
WORKDIR /app

# Сначала копируем только файлы зависимостей
COPY pyproject.toml uv.lock ./

# Объявляем аргумент сборки из Docker Compose
ARG ENV

# Устанавливаем зависимости в зависимости от окружения
RUN if [ "$ENV" = "prod" ]; then \
      uv sync --no-dev; \
    else \
      uv sync --all-groups --link-mode=copy; \
    fi

ENV PATH="/app/.venv/bin:$PATH"

# Копируем код приложения в отдельном слое
COPY . .
