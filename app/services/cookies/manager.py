# app/services/cookies/manager.py

import asyncio
from typing import Dict, Optional

from app.core.logger import logger
from .cookies import check_existing, get_new, load_cookies

class CookieManager:
    """
    Простой, но надежный менеджер cookies.
    Проверяет валидность перед каждым использованием.
    """
    def __init__(self):
        self._cookies: Optional[Dict] = None
        self._lock = asyncio.Lock()

    async def get_valid_cookies(self) -> Optional[Dict]:
        """
        Гарантирует, что возвращаемые куки валидны ПРЯМО СЕЙЧАС.
        """
        async with self._lock:
            # Проверяем куки из файла. Это наш единственный источник правды.
            if await check_existing():
                logger.info("Cookie check successful. Loading from file.")
                self._cookies = await load_cookies()
            else:
                # Если проверка провалилась - без разговоров идем за новыми.
                logger.warning("Cookie check failed or file not found. Getting new ones.")
                self._cookies = await get_new()

            if not self._cookies:
                logger.error("CRITICAL: Failed to get any valid cookies.")

            return self._cookies

# Создаем единственный экземпляр
cookie_manager = CookieManager()