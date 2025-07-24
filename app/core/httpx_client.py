# app/core/httpx_client.py

import json
import httpx
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.logger import logger


class HTTPXClient:
    _instance: Optional[httpx.AsyncClient] = None

    @classmethod
    async def initialize(cls):
        if cls._instance is None:
            cls._instance = httpx.AsyncClient(timeout=30.0, verify=False)

    @classmethod
    async def shutdown(cls):
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._instance is None:
            raise RuntimeError("HTTP-клиент не инициализирован.")
        return cls._instance

    @classmethod
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=lambda retry_state: logger.warning(
            f"[HTTPXClient] Retrying request {retry_state.attempt_number} for {retry_state.args[1]} ({retry_state.outcome.exception()})"
        )
    )
    async def fetch(
            cls,
            url: str,
            method: str = "GET",
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] | str = None,
    ) -> Dict[str, Any]:

        try:
            client = cls.get_client()
            response = await client.request(
                method=method, url=url, params=params, data=data, headers=headers, cookies=cookies
            )
            response.raise_for_status()

            json_data = None
            if "application/json" in response.headers.get("Content-Type", ""):
                try:
                    json_data = response.json()
                except ValueError:
                    json_data = None
            elif "text/html" in response.headers.get("Content-Type", ""):
                try:
                    json_data = json.loads(response.text)
                except ValueError:
                    json_data = None

            return dict(
                status_code=response.status_code, headers=dict(response.headers),
                cookies=dict(response.cookies), text=response.text, json=json_data
            )
        except httpx.HTTPStatusError as e:
            # Локальный импорт для разрыва циклической зависимости
            from app.services.cookies.manager import cookie_manager

            if e.response.status_code in [401, 403]:
                await cookie_manager.invalidate_cache()

            raise e
        except Exception as e:
            logger.error(f"Unhandled exception in HTTPXClient.fetch: {e}", exc_info=True)
            raise e