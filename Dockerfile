FROM python:3.11-slim


WORKDIR /app


# Обновите pip до актуальной версии
RUN pip install --upgrade pip


# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --retries 5 -r requirements.txt


COPY . .

# Если есть .dockerignore — он исключит ненужные файлы (__pycache__, .git, etc.)


# 7. Создание непривилегированного пользователя (безопасность)
RUN adduser --disabled-password --gecos '' django-user
USER django-user


# 8. Настройка окружения (переменные, которые можно переопределить при запуске)
ENV PYTHONDUNREDIRECTIO=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=Course_FirstProject.settings.production


# 9. Открытие порта (обычно 8000 для Gunicorn)
EXPOSE 8000

# Примечание: реальный проброс портов делается через docker run -p 8000:8000


# 10. Команда запуска (Gunicorn + настройки)
CMD ["gunicorn", "Course_FirstProject.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
