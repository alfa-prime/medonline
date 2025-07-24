import re
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import htmlmin
from app.core.config import get_settings
from app.core.httpx_client import HTTPXClient
from app.core.logger import logger
from app.services.cookies.manager import cookie_manager

settings = get_settings()

LOG_TEST_NAME = "MEDTEST"


async def parse_html_test_result(html_raw: str):
    soup = BeautifulSoup(html_raw, "lxml")

    for tag in soup(["script", "style", "form", "meta"]):
        tag.decompose()

    for tag in soup.find_all("div", class_=["parametervalue", "combobox-parameter", "input-area"]):
        tag.decompose()

    for tag in soup.find_all(["span", "div"]):
        if not tag.attrs:
            tag.unwrap()

    for tag in soup.find_all(True):
        tag.attrs = {key: value for key, value in tag.attrs.items() if
                     key not in ["style", "class", "id", "data-mce-style"]}

    html_code = soup.prettify()
    html_code = re.sub(r"\n\s*\n", "\n", html_code).strip()
    html_code = htmlmin.minify(html_code, remove_empty_space=True)
    return html_code


async def get_tests_result(test_id: str, cookies: dict):
    try:
        url = settings.BASE_URL
        params = {"c": "EvnXml", "m": "doLoadData"}
        data = {"EvnXml_id": test_id}
        response = await HTTPXClient.fetch(url=url, method="POST", params=params, cookies=cookies, data=data)
        if response["status_code"] != 200 or "json" not in response:
            return None

        html_code = await parse_html_test_result(response["json"].get("html", ""))
        return html_code if html_code else None

    except Exception as e:
        logger.error(f"{LOG_TEST_NAME} : Error getting test result {test_id}: {e}")
        return None


async def get_patient_tests(cookies, last_name: str, first_name: str, middle_name: str, birthday: str):
    try:
        url = settings.BASE_URL
        params = {"c": "Search", "m": "searchData"}
        data = {
            "PersonPeriodicType_id": "1",
            "SearchFormType": "EvnUslugaPar",
            "Person_Surname": last_name,
            "Person_Firname": first_name,
            "Person_Secname": middle_name,
            "Person_Birthday": birthday,
            "LpuSection_uid": "3010101000003273",
            "SearchType_id": "1",
            "Part_of_the_study": "false",
            "PersonCardStateType_id": "1",
            "limit": "100",
            "start": "0",
        }

        response = await HTTPXClient.fetch(url=url, method="POST", params=params, cookies=cookies, data=data)
        if response["status_code"] != 200 or "json" not in response:
            return None

        data = response["json"]
        if not data or "data" not in data or not data["data"]:
            return None

        return await sanitize_data(data, cookies)

    except Exception as e:
        logger.error(f"{LOG_TEST_NAME} : Error getting patient results: {e}")
        return None


async def sanitize_data(data: dict, cookies: dict) -> dict | None:
    tests = [test for test in data.get("data", []) if test.get("EvnXml_id")]

    if not tests:
        return None

    person_data = tests[0]

    last_name = person_data.get("Person_Surname", "").capitalize()
    first_name = person_data.get("Person_Firname", "").capitalize()
    middle_name = person_data.get("Person_Secname", "").capitalize() if person_data.get("Person_Secname") else ""
    birthday = person_data.get("Person_Birthday", "")
    age = person_data.get("Person_Age", "")

    tasks = [get_tests_result(test.get("EvnXml_id"), cookies) for test in tests]
    logger.info(f"{LOG_TEST_NAME} : Fetching {len(tasks)} test results for {last_name} in parallel...")
    results = await asyncio.gather(*tasks)
    logger.info(f"{LOG_TEST_NAME} : All {len(tasks)} results received.")

    sanitized_tests = {}
    tests_dates = []

    for test, test_result in zip(tests, results):
        if test_result is None:
            continue

        test_date_str = test.get("EvnUslugaPar_setDate")
        try:
            date_obj = datetime.strptime(test_date_str, "%d.%m.%Y")
            test_date = date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            logger.error(f"{LOG_TEST_NAME} : Invalid test_date format {test_date_str}")
            continue

        if test_date not in tests_dates:
            tests_dates.append(test_date)

        test_info = {
            "service": test.get("MedService_Name", "No data"),
            "analyzer_name": test.get("Resource_Name", "No data"),
            "test_code": test.get("Usluga_Code", "No data"),
            "test_name": test.get("Usluga_Name", "No data"),
            "test_result": test_result,
        }
        sanitized_tests.setdefault(test_date, []).append(test_info)

    if not sanitized_tests:
        return None

    tests_dates.sort(reverse=True)
    logger.info(f"{LOG_TEST_NAME} : Results for patient {last_name} {first_name} {middle_name} got successfully")

    return {
        "person": {
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": middle_name,
            "birthday": birthday,
            "age": age,
        },
        "tests_total": len(tests),
        "tests_dates": tests_dates,
        "tests_dates_latest": max(tests_dates, default=None),
        "tests_with_results": sanitized_tests,
    }





