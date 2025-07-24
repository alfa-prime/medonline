# app/services/cookies/manager.py

import asyncio
import time
from typing import Dict, Optional

from app.core.logger import logger
from .cookies import get_new, load_cookies, check_existing


class CookieManager:
    def __init__(self, check_interval_seconds: int = 900):  # 15 минут
        self._cookies: Optional[Dict] = None
        self._lock = asyncio.Lock()
        self._last_check_time: float = 0
        self._check_interval = check_interval_seconds

    async def invalidate_cache(self):
        """Принудительно сбрасывает кэш (вызывается из HTTPXClient при 401/403)."""
        async with self._lock:
            if self._cookies is not None:
                logger.warning("Invalidating cookie cache due to an authentication error (401/403).")
                self._cookies = None
                self._last_check_time = 0

    async def get_valid_cookies(self) -> Optional[Dict]:
        """Основной метод с гибридной логикой."""
        async with self._lock:
            now = time.time()
            if self._cookies and (now - self._last_check_time < self._check_interval):
                logger.info("Using cached cookies (within check interval).")
                return self._cookies

            logger.info("Cache is empty or check interval elapsed. Verifying cookies...")
            if await check_existing():
                logger.info("Existing cookies from file are valid.")
                self._cookies = await load_cookies()
            else:
                logger.warning("Cookies are invalid or not found. Getting new ones.")
                self._cookies = await get_new()

            if self._cookies:
                self._last_check_time = time.time()
                logger.info("Cookies are set and cached.")
            else:
                logger.error("Failed to get any valid cookies.")

            return self._cookies

    def get_status(self) -> Dict:
        """Возвращает статус для дашборда (если он будет)."""
        return {"has_valid_cookies": self._cookies is not None}


cookie_manager = CookieManager()