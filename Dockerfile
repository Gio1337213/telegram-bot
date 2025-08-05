# Используем официальный Python 3.10 образ
FROM python:3.10.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Команда запуска (замени на свой файл, если нужно)
CMD ["python", "bot.py"]