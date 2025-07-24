from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.httpx_client import HTTPXClient
from app.core.logger import logger
from app.route import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    """
    Управление жизненным циклом приложения:
    - Инициализация HTTPXClient при старте
    - Закрытие HTTPXClient при завершении
    """
    await HTTPXClient.initialize()  # Запускаем клиент
    logger.info("HTTPXClient инициализирован")
    yield  # Приложение работает
    await HTTPXClient.shutdown()  # Закрываем клиент при завершении работы
    logger.info("HTTPXClient закрыт")


tags_metadata = [
    {"name": "Complex results",
     "description": "Получение результатов анализов, функциональных тестов, УЗИ и рентгенографии"},
]

app = FastAPI(
    openapi_tags=tags_metadata,
    title="Medical Extractor",
    description="Medical Extractor",
    lifespan=lifespan
)

app.mount("/dashboard-static", StaticFiles(directory="dashboard"), name="dashboard-static")


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def get_dashboard_page():
    with open("dashboard/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)


# Подключаем маршруты API
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
