# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt requirements-dev.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir flake8 black pytest && \
    pip install --no-cache-dir -r requirements-dev.txt || true

# Копируем весь код проекта
COPY . .

# Запускаем линтер и тесты при сборке
RUN flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
RUN pytest -v

# Команда по умолчанию для запуска бота
CMD ["python", "bot.py"]