""""인증 관련 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.error import AppError, RegionError
from ..schemas.auth import LoginCheckResponse, UserCreateRequest, UserLoginRequest
from ..schemas.user import UserInfo
from ..dependencies import get_current_user_session
from ..core.exception import AppException
from ..core import session
from ..crud.user import create_user, get_user_by_cuid, get_user_by_email


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get(
    "/check",
    summary="로그인 상태 조회",
    status_code=status.HTTP_200_OK,
)
def login_check(
    request: Request,
    db: Session = Depends(get_db),
) -> LoginCheckResponse:
    """로그인 상태 조회 함수."""

    is_logged_in = False
    user = None
    try:
        session = get_current_user_session(request)
        user = get_user_by_cuid(db, session.cuid)
        is_logged_in = True if user else False
    except:
        pass

    return {
        "is_logged_in": is_logged_in,
        "user": user,
    }


@router.post(
    "/signup",
    summary="회원가입",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: { "model": RegionError, "description": "지원하지 않는 동네인 경우" },
        409: { "model": AppError, "description": "이미 가입된 이메일인 경우" },
    },
)
def signup(
    body: UserCreateRequest,
    db: Session = Depends(get_db),
) -> UserInfo:
    """회원가입 처리 함수. 이메일 중복 체크 및 동네 검증 후 사용자 생성."""
    user, created = create_user(db, body)
    if not created:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            message="이미 등록된 이메일입니다.",
        )
    return user


@router.post(
    "/login",
    summary="로그인 (세션 발급)",
    status_code=status.HTTP_200_OK,
    responses={
        401: { "model": AppError, "description": "유효한 자격 증명이 아닌 경우" },
    },
)
def login(
    body: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> UserInfo:
    """로그인 처리 함수. 이메일과 비밀번호 검증 후 세션 발급."""
    user = get_user_by_email(db, body.email)
    if not user or not user.verify_password(body.password):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="이메일 또는 비밀번호가 잘못되었습니다.",
        )
    session.login(request, user)
    return user


@router.post(
    "/logout",
    summary="로그아웃 (세션 삭제)",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
):
    """로그아웃 처리 함수. 세션 삭제."""
    session.logout(request)
    return
