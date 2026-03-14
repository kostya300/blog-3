FROM python:3.11-slim

WORKDIR /app

# Системные зависимости для psycopg, Pillow и др.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# Обновляем pip
RUN pip install --upgrade pip

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --retries 5 -r requirements.txt

# Копируем всё приложение
COPY . .

# Создание непривилегированного пользователя
RUN adduser --disabled-password --gecos '' django-user
USER django-user

# Базовые переменные окружения (можно переопределить при запуске)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=Course_FirstProject.settings

# Открываем порт 8000
EXPOSE 8000

# Команда запуска (для простого деплоя можно использовать runserver)
# Для продакшена лучше установить gunicorn в requirements.txt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
