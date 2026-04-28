"""애플리케이션 팩토리 및 FastAPI 인스턴스 정의 모듈."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from .models import Base
from .database import engine
from .routers import (
    scalar,
    sample,
    health,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    yield 전 코드: 앱 시작 전 실행됨
    yield 후 코드: 앱 종료 전 실행됨
    """

    # 데이터베이스 내 테이블 자동 생성
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    """FastAPI 앱 생성 및 라우터를 등록 후 반환."""
    app = FastAPI(
        title="fastapi",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Scalar 문서는 OpenAPI 목록에서 숨김
    app.include_router(scalar.router, prefix="/scalar", include_in_schema=False)
    app.include_router(sample.router)
    app.include_router(health.router)

    return app


app = create_app()
