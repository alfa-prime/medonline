# app/services/cookies/cookies.py

import json
from pathlib import Path
from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()

COOKIES_FILE = Path(settings.COOKIES_FILE)
BASE_URL = settings.BASE_URL


async def get_new():
    # Локальный импорт для разрыва циклической зависимости
    from app.core.httpx_client import HTTPXClient
    cookies = None
    try:
        # get first part of cookies
        url = BASE_URL
        params = {"c": "portal", "m": "promed", "from": "promed"}
        response = await HTTPXClient.fetch(url=url, method="GET", params=params)
        cookies = {k: v for k, v in response['cookies'].items()}

        # authorize
        url = BASE_URL
        headers = {
            "Origin": "https://evmias.fmba.gov.ru",
            "Referer": "https://evmias.fmba.gov.ru/?c=promed",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "*/*",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",
            "Content-Type": "text/x-gwt-rpc; charset=utf-8",
        }
        params = {
            "c": "main", "m": "index", "method": "Logon", "login": settings.EVMIAS_LOGIN
        }
        data = {
            "login": settings.EVMIAS_LOGIN, "psw": settings.EVMIAS_PASSWORD,
        }
        response = await HTTPXClient.fetch(
            url=url, method="POST", headers=headers, cookies=cookies, params=params, data=data
        )
        if not (response['status_code'] == 200 and "true" in response['text']):
            logger.error("Authorization failed")
            raise RuntimeError("Authorization failed")
        logger.info("Authorization success")
        cookies.update({"login": settings.EVMIAS_LOGIN})

        # get second part of cookies
        url = f"{BASE_URL}ermp/servlets/dispatch.servlet"
        headers = {
            "Origin": "https://evmias.fmba.gov.ru",
            "Referer": "https://evmias.fmba.gov.ru/?c=promed",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "*/*",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",
            "Content-Type": "text/x-gwt-rpc; charset=utf-8",
            "X-Gwt-Permutation": settings.EVMIAS_PERMUTATION,
            "X-Gwt-Module-Base": "https://evmias.fmba.gov.ru/ermp/",
        }
        data = settings.EVMIAS_SECRET
        response = await HTTPXClient.fetch(url=url, method="POST", headers=headers, cookies=cookies, data=data)

        if response['status_code'] != 200:
            logger.error(f"Error getting final cookies: status {response['status_code']}")
            raise RuntimeError(f"Error getting final cookies")

        cookies.update({k: v for k, v in response.get('cookies', {}).items()})
        logger.info("Got final cookies")

        COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with COOKIES_FILE.open("w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False)
        logger.info(f"Cookies saved to {COOKIES_FILE}")

    except Exception as e:
        logger.error(f"Error getting new cookies: {e}", exc_info=True)
        return None
    return cookies


async def load_cookies() -> dict:
    if not COOKIES_FILE.exists():
        return {}
    try:
        with COOKIES_FILE.open("r", encoding="utf-8") as f:
            cookies = json.load(f)
        return cookies if isinstance(cookies, dict) else {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


async def check_existing() -> bool:
    """Проводит легковесную проверку валидности кук из файла."""
    # Локальный импорт
    from app.core.httpx_client import HTTPXClient

    cookies = await load_cookies()
    if not cookies:
        return False

    logger.info("Performing proactive cookie check...")
    url = settings.BASE_URL
    headers = {
        "Origin": "https://evmias.fmba.gov.ru",
        "Referer": "https://evmias.fmba.gov.ru/?c=promed",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Accept": "*/*",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0",
        "Content-Type": "text/x-gwt-rpc; charset=utf-8",
    }
    params = {"c": "Common", "m": "getCurrentDateTime"}
    data = {"is_activerules": "true"}

    try:
        response = await HTTPXClient.fetch(url=url, method="POST", params=params, cookies=cookies, data=data, headers=headers)
        if response["status_code"] == 200 and response.get("json") is not None:
            logger.info("Proactive check successful: cookies are valid.")
            return True
        logger.warning("Proactive check failed: cookies are invalid.")
        return False
    except Exception as e:
        logger.error(f"Error during proactive cookie check: {e}")
        return False