"""데모용 함수 모음"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from .config import GUEST_LOGIN_ENABLE
from .database import get_db
from .models import User
from .core import session
from .crud.user import get_user_by_cuid
from .schemas.error import NotFoundError
from .schemas.user import UserInfo


GUEST_CUID = "guest"
GUEST_EMAIL = "guest@example.com"
GUEST_USERNAME = "guest"
GUEST_PASSWORD = "guest"


# fns

def create_guest_user(db: Session):
    """
    게스트 사용자 생성
    """

    if not GUEST_LOGIN_ENABLE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )

    created = False
    guest = get_user_by_cuid(db, GUEST_CUID) or User()
    guest.cuid = GUEST_CUID
    guest.name = GUEST_USERNAME
    guest.email = GUEST_EMAIL
    guest.password = GUEST_PASSWORD
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest, created

def get_guest_user(db: Session):
    """
    게스트 사용자 조회
    """

    user, _ = create_guest_user(db)
    return user


# router

router = APIRouter(
    tags=["demo"],
    responses={
        404: { "model": NotFoundError, "description": "게스트 로그인이 비활성화된 경우" },
    }
)

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
