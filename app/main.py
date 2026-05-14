"""애플리케이션 팩토리 및 FastAPI 인스턴스 정의 모듈."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from .models import Base
from .database import engine, SessionLocal
from .core.exception import AppException
from .schemas.error import AppError
from .dependencies import get_current_user_session
from .routers import (
    scalar,
    health,
    public,
    auth,
    users,
    recommendations,
)

from . import demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    yield 전 코드: 앱 시작 전 실행됨
    yield 후 코드: 앱 종료 전 실행됨
    """

    # 데이터베이스 내 테이블 자동 생성
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        demo.create_guest_user(db)
    except:
        pass
    finally:
        db.close()

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

    # http_only는 항상 설정됨: https://starlette.dev/middleware/#sessionmiddleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "x"),
        session_cookie="session",
        same_site="lax",                                  # CSRF 방어
        https_only=os.getenv("APP_ENV") == "production",  # 운영 모드에서만 True
        max_age=60 * 60 * 24,                             # 1일 동안 세션 유지
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

    def require_auth(router: APIRouter):
        """로그인 전용 라우터 자동 구성"""
        app.include_router(
            router,
            dependencies=[Depends(get_current_user_session)],
            responses={
                401: {"model": AppError, "description": "로그인이 되어있지 않은 경우"},
            },
        )

    # Scalar 문서는 OpenAPI 목록에서 숨김
    app.include_router(scalar.router, prefix="/scalar", include_in_schema=False)
    app.include_router(health.router)
    app.include_router(public.router)
    app.include_router(demo.router)
    app.include_router(auth.router)
    require_auth(users.router)
    require_auth(recommendations.router)
    return app


app = create_app()
