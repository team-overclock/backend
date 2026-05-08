"""사용자 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from ..models import User
from ..database import get_db
from ..core import session
from ..core.exception import AppException
from ..core.validate import verify_region
from ..schemas.error import AppError, RegionError
from ..schemas.user import UserInfoUpdateRequest, UserInfo, UserPasswordChangeRequest
from ..dependencies import only_self_access

router = APIRouter(
    prefix="/users/me",
    tags=["users"],
    responses={
        403: { "model": AppError, "description": "접근 권한이 없는 경우" },
    },
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
def user_info(
    request: Request,
    user: User = Depends(only_self_access),
) -> UserInfo:
    """사용자 정보 조회"""
    return user


@router.patch(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        400: { "model": RegionError, "description": "지원하지 않는 동네인 경우" },
    }
)
def user_info_update(
    body: UserInfoUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
) -> UserInfo:
    """사용자 정보 수정"""
    if body.name:
        user.name = body.name
    if body.email:
        user.email = body.email
    if "region_id" in body.model_dump(exclude_unset=True):
        user.region = verify_region(db, body.region_id, 2)

    db.commit()
    db.refresh(user)
    return user



@router.post(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: { "model": AppError, "description": "현재 비밀번호가 일치하지 않는 경우" },
    }
)
def user_password_change(
    body: UserPasswordChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
):
    """비밀번호 변경"""
    if not body.current_password or not user.verify_password(body.current_password):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="현재 비밀번호가 일치하지 않습니다.",
        )
    user.password = body.new_password
    db.commit()
    # session.logout(request)  # 비밀번호 변경 후 세션 만료 (재로그인 요구)
    return
