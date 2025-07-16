from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health check"])


@router.get("/ping", status_code=200)
def pong():
    return {"status": "ok"}
