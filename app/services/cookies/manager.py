import asyncio
import time
from typing import Dict, Optional

from app.core.logger import logger
from .cookies import check_existing, get_new, load_cookies


class CookieManager:
    """
    Управляет жизненным циклом cookies, кэшируя их в памяти,
    чтобы избежать лишних запросов на аутентификацию.
    """

    def __init__(self, check_interval_seconds: int = 300):  # Проверять раз в 5 минут
        self._cookies: Optional[Dict] = None
        self._last_check_time: float = 0
        self._lock = asyncio.Lock()  # Защита от одновременного обновления cookies из разных запросов
        self._check_interval = check_interval_seconds

    async def get_valid_cookies(self) -> Optional[Dict]:
        """
        Основной метод для получения валидных cookies.
        Использует кэш и периодическую проверку.
        """
        async with self._lock:
            now = time.time()
            # 1. Если есть кэш и он не "протух", возвращаем его сразу
            if self._cookies and (now - self._last_check_time < self._check_interval):
                logger.info("Using cached cookies.")
                return self._cookies

            logger.info("Checking or refreshing cookies...")

            # 2. Пытаемся загрузить из файла и проверить их валидность
            if await check_existing():
                logger.info("Existing cookies from file are valid.")
                self._cookies = await load_cookies()
            else:
                # 3. Если куки невалидны или отсутствуют, получаем новые
                logger.warning("Existing cookies are invalid or not found. Getting new ones.")
                self._cookies = await get_new()

            if self._cookies:
                self._last_check_time = now  # Обновляем время последней успешной проверки/получения
                logger.info("Cookies are set and cached.")
            else:
                logger.error("Failed to get any valid cookies.")

            return self._cookies


# Создаем ЕДИНСТВЕННЫЙ экземпляр менеджера для всего приложения.
# Это гарантирует, что все запросы будут использовать один и тот же кэш.
cookie_manager = CookieManager(check_interval_seconds=600)  # Проверяем раз в 10 минут