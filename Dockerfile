FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Установка netcat-openbsd (вместо netcat)
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Сборка статики — работает благодаря default SECRET_KEY в settings.py
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "Course_FirstProject.wsgi:application", "--bind", "0.0.0.0:8000"]