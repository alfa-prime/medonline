# Используем минимальный Python 3.10 образ для сборки зависимостей
FROM python:3.10-slim AS builder

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /code

# Отключаем кеширование .pyc файлов (ускоряет работу в контейнере)
# Отключаем буферизацию вывода Python (чтобы логи сразу отображались)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH"

# Копируем файл с зависимостями в контейнер
COPY ./requirements.txt /code/requirements.txt

# Обновляем pip и устанавливаем зависимости без кеширования
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r /code/requirements.txt \
    && rm -rf /root/.cache/pip


# Финальный образ без сборочных инструментов
FROM python:3.10-slim

# Install micro text editor and clean up cache to reduce image size
RUN apt-get update && apt-get install -y micro postgresql-client\
    && rm -rf /var/lib/apt/lists/*


# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /code

# Наследуем переменные окружения из builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH"

# Копируем установленные библиотеки из промежуточного контейнера
COPY --from=builder /install /usr/local

# Копируем код приложения в контейнер
COPY ./app /code/app
