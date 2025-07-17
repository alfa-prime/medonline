import json
from pathlib import Path
from app.core.config import get_settings
from app.core.logger import logger
from app.core.httpx_client import HTTPXClient


settings = get_settings()

COOKIES_FILE = Path(settings.COOKIES_FILE)
BASE_URL = settings.BASE_URL

async def get_new():
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
            "X-Requested-With": "XMLHttpRequest",  # Тоже важный заголовок из реального запроса
        }
        params = {
            "c": "main",
            "m": "index",
            "method": "Logon",
            "login": settings.EVMIAS_LOGIN
        }

        data = {
            "login": settings.EVMIAS_LOGIN,
            "psw": settings.EVMIAS_PASSWORD,
            "swUserRegion": "",
            "swUserDBType": "",
        }

        response = await HTTPXClient.fetch(
            url=url,
            method="POST",
            headers=headers,
            cookies=cookies,
            params=params,
            data=data
        )
        if response['status_code'] == 200 and "true" in response['text']:
            logger.info("Authorization success")
        else:
            logger.error("Authorization failed")
            raise RuntimeError("Authorization failed")

        cookies.update({"login": settings.EVMIAS_LOGIN})

        # get second part of cookies
        url = f"{BASE_URL}ermp/servlets/dispatch.servlet"
        headers = {
            "Content-Type": "text/x-gwt-rpc; charset=utf-8",
            "X-Gwt-Permutation": settings.EVMIAS_PERMUTATION,
            "X-Gwt-Module-Base": "https://evmias.fmba.gov.ru/ermp/",
        }
        data = settings.EVMIAS_SECRET
        response = await HTTPXClient.fetch(url=url, method="POST", headers=headers, cookies=cookies, data=data)

        if response['status_code'] != 200:
            logger.error(f"Error get final cookies: status {response['status_code']}")
            raise RuntimeError(f"Error get final cookies: status {response['status_code']}")

        cookies.update({k: v for k, v in response.get('cookies').items()})
        logger.info("Got final cookies")

        # save cookies in file
        COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with COOKIES_FILE.open("w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False)
        logger.info(f"Cookies saved to {COOKIES_FILE}")

    except Exception as e:
        logger.error(f"Error get cookies: {e}", exc_info=True)

    return cookies

async def check_existing() -> bool:
    if not COOKIES_FILE.exists():
        logger.info(f"Cookies file not found in path: {COOKIES_FILE}")
        return False

    try:
        with COOKIES_FILE.open("r", encoding="utf-8") as f:
            cookies = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Reading cookies file {COOKIES_FILE} error: invalid JSON")
        return False
    except Exception as e:
        logger.error(f"Error reading cookies file: {str(e)}")
        return False

    logger.info("Checking existing cookies")

    url = settings.BASE_URL

    params = {"c": "Common", "m": "getCurrentDateTime"}
    data = {"is_activerules": "true"}

    try:
        response = await HTTPXClient.fetch(url=url, method="POST", params=params, cookies=cookies, data=data)
        if response["status_code"] == 200 and response["json"] is not None:
            return True
        logger.error("Cookies not valid")
        return False
    except Exception as e:
        logger.error(f"Error checking cookies: {str(e)}")
        return False


async def load_cookies() -> dict:
    if not COOKIES_FILE.exists():
        logger.info(f"Cookies file not found in path: {COOKIES_FILE}")
        return {}
    try:
        with COOKIES_FILE.open("r", encoding="utf-8") as f:
            cookies = json.load(f)
        if not isinstance(cookies, dict):
            logger.error(f"Invalid cookies format in {COOKIES_FILE}")
            return {}
        logger.info(f"Cookies loaded from {COOKIES_FILE}")
        return cookies
    except json.JSONDecodeError:
        logger.error(f"Reading cookies file {COOKIES_FILE} error: invalid JSON")
        return {}
    except Exception as e:
        logger.error(f"Error reading cookies file: {str(e)}")
        return {}


async def set_cookies() -> dict | None:
    try:
        if await check_existing():
            logger.info("Current cookies is valid")
            cookies = await load_cookies()
            if not cookies:
                logger.error("No valid cookies found, getting new ones...")
                cookies = await get_new()
        else:
            logger.info("Current cookies invalid, getting new ones..")
            cookies = await get_new()

        return cookies if cookies else None
    except Exception as e:
        logger.debug(f"Error setting cookies: {e}", exc_info=True)
        return None
