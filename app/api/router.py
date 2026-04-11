"""API 라우터를 모아 앱에 연결하는 모듈."""

from fastapi import APIRouter

from .routes.health import router as health_router
from .routes.sample import router as sample_router

# 애플리케이션 전체 API 엔드포인트를 포함하는 상위 라우터.
api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(sample_router)
