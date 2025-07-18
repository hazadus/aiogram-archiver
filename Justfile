# Запустить бота в режиме разработки
dev:
  docker compose --profile dev up

# Посчитать строки кода в проекте и сохранить в файл
cloc:
    cloc --fullpath --exclude-list-file=.clocignore --md . > cloc.md

# Форматировать код с помощью black и isort
format:
    @echo "🧹 Форматирование кода..."
    cd bot && uv run black app
    cd bot && uv run isort app
    @echo "✅ Код отформатирован"

# Проверить код с помощью ruff и mypy
lint:
    @echo "🔍 Проверка кода с помощью ruff..."
    cd bot && uv run ruff check app
    @echo "🔍 Проверка кода с помощью mypy..."
    cd bot && uv run mypy app
    @echo "✅ Код проверен"

# Сгенерировать сообщение коммита (см. https://github.com/hazadus/gh-commitmsg)
commitmsg:
    gh commitmsg --language russian --examples