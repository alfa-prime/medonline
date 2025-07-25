from fastapi import APIRouter
from .health import router as health_router
from .complex import router as complex_test_router

router = APIRouter(prefix="/api")
router.include_router(health_router)
router.include_router(complex_test_router)
