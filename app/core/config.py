from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Класс конфигурации приложения.
    Использует `pydantic.BaseSettings` для автоматической загрузки переменных окружения
    и их валидации.

    Пример `.env` файла:
    ```
    COOKIES_FILE=/path/to/cookies.json
    ```

    Использование:
    ```python
    from app.core.config import get_settings

    settings = get_settings()
    print(settings.COOKIES_FILE)  # Выведет путь из `.env` или переменной окружения
    ```
    """
    BASE_URL: str
    EVMIAS_LOGIN: str
    EVMIAS_PASSWORD: str
    EVMIAS_SECRET: str
    EVMIAS_PERMUTATION: str
    COOKIES_FILE: str

    model_config = SettingsConfigDict(
        env_file=".env",  # Автоматически загружает переменные из .env
        env_file_encoding="utf-8"  # Поддержка UTF-8
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Получает объект конфигурации с кэшированием.
    Использует `lru_cache()`, чтобы загружать настройки только **один раз** при запуске приложения.
    Это оптимизирует работу FastAPI и уменьшает нагрузку на систему.
    """
    return Settings()
