"""애플리케이션 팩토리 및 FastAPI 인스턴스 정의 모듈."""

from fastapi import FastAPI

from .routers import (
    scalar,
    sample,
    health,
)


def create_app() -> FastAPI:
    """FastAPI 앱 생성 및 라우터를 등록 후 반환."""
    app = FastAPI(
        title="fastapi",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Scalar 문서는 OpenAPI 목록에서 숨김
    app.include_router(scalar.router, prefix="/scalar", include_in_schema=False)
    app.include_router(sample.router)
    app.include_router(health.router)

    return app


app = create_app()
