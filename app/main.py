"""애플리케이션 팩토리 및 FastAPI 인스턴스 정의 모듈."""

from fastapi import FastAPI

from .api.router import api_router
from .docs.scalar import router as scalar_router


def create_app() -> FastAPI:
    """FastAPI 앱 생성 및 라우터를 등록 후 반환."""
    app = FastAPI(
        title="fastapi",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Scalar 문서는 OpenAPI 목록에서 숨김
    app.include_router(scalar_router, prefix="/scalar", include_in_schema=False)
    app.include_router(api_router)

    return app


app = create_app()
