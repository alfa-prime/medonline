import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

APP_LOG_FILE = Path("logs/app.log")
ERROR_LOG_FILE = Path("logs/errors.log")


def read_last_log_lines(file_path: Path, num_lines: int = 50) -> list[str]:
    """Читает последние N строк из файла, если он существует."""
    if not file_path.exists():
        return [f"Log file not found: {file_path.name}"]
    try:
        with file_path.open('r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines[-num_lines:]]
    except Exception as e:
        return [f"Error reading log file {file_path.name}: {e}"]


def get_dashboard_data():
    """Собирает все данные для дашборда."""
    return {
        "app_logs": read_last_log_lines(APP_LOG_FILE),
        "error_logs": read_last_log_lines(ERROR_LOG_FILE),
        "fastapi_status": "ONLINE",
    }


@router.get("/status")
async def get_dashboard_status():
    return get_dashboard_data()


@router.get("/stream")
async def stream_updates(request: Request):
    """Отправляет обновления по SSE, когда содержимое лог-файлов меняется."""

    async def event_generator():
        last_data_json = ""
        while True:
            if await request.is_disconnected():
                break

            current_data = get_dashboard_data()
            current_data_json = json.dumps(current_data)

            if current_data_json != last_data_json:
                yield {"event": "update", "data": current_data_json}
                last_data_json = current_data_json

            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
