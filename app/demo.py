"""데모용 함수 모음"""

import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from .database import get_db
from .core import session
from .core.exception import AppException
from .crud.user import create_user
from .schemas.auth import UserCreateRequest
from .schemas.user import UserInfo


load_dotenv()

GUEST_LOGIN_ENABLE = (os.getenv("GUEST_LOGIN_ENABLE") or "false").lower() == "true"
GUEST_EMAIL = os.getenv("GUEST_EMAIL") or "guest@example.com"
GUEST_USERNAME = os.getenv("GUEST_USERNAME")
GUEST_PASSWORD = os.getenv("GUEST_PASSWORD") or "guest"


# fns

def create_guest_user(db: Session):
    """
    게스트 사용자 생성
    """

    if not GUEST_LOGIN_ENABLE:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="현재 게스트 로그인 기능이 비활성화 상태입니다.",
        )

    return create_user(db, UserCreateRequest(
        name=GUEST_USERNAME,
        email=GUEST_EMAIL,
        password=GUEST_PASSWORD,
    ))

def get_guest_user(db: Session):
    """
    게스트 사용자 조회
    """

    user, _ = create_guest_user(db)
    return user


# router

router = APIRouter(tags=["demo"])

@router.post(
    "/auth/guest",
    summary="게스트 로그인 (세션 발급)",
    status_code=status.HTTP_200_OK,
    tags=["auth"],
)
def guest_login(
    request: Request,
    db: Session = Depends(get_db),
) -> UserInfo:
    """게스트 로그인 처리 함수"""
    user = get_guest_user(db)
    session.login(request, user)
    return user
