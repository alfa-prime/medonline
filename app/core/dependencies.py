from typing import Dict, Any
from fastapi import HTTPException, status
from app.services.cookies.manager import cookie_manager
from app.core.logger import logger

async def get_valid_cookies_dependency() -> Dict[str, Any]:
    """
    Зависимость FastAPI для получения валидных cookies.
    Автоматически обрабатывает ошибки и кэширование.
    """
    cookies = await cookie_manager.get_valid_cookies()
    if not cookies:
        logger.critical("Could not authenticate with the external service. No cookies available.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not authenticate with the external service. Please try again later.",
        )
    return cookies