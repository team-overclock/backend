"""애플리케이션 팩토리 및 FastAPI 인스턴스 정의 모듈."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .models import Base
from .database import engine
from .core.exception import AppException
from .routers import (
    scalar,
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
        redirect_slashes=False,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 기본 에러 구조 변경
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, str):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "message": detail,
                    "detail": None,
                },
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": detail,
            },
        )

    # 커스텀 에러 등록
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    # Scalar 문서는 OpenAPI 목록에서 숨김
    app.include_router(scalar.router, prefix="/scalar", include_in_schema=False)
    app.include_router(health.router)

    return app


app = create_app()
