"""사용자 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from ..models import User, UserRecommendation
from ..database import get_db
from ..core import session
from ..core.exception import AppException
from ..core.validate import verify_region
from ..crud.service import get_user_recommendations_by_user_id
from ..schemas.error import AppError, RegionError
from ..schemas.user import UserInfoUpdateRequest, UserInfo, UserPasswordChangeRequest
from ..schemas.service import UserRecommendations
from ..dependencies import only_self_access, get_current_user_recommendations

router = APIRouter(
    prefix="/users/me",
    tags=["users"],
    responses={
        403: { "model": AppError, "description": "접근 권한이 없는 경우" },
    },
)


@router.get(
    "",
    summary="사용자 정보 조회",
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
    summary="사용자 정보 수정",
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
        user.region = None if body.region_id is None else verify_region(db, body.region_id, 2)

    db.commit()
    db.refresh(user)
    return user



@router.post(
    "/password",
    summary="비밀번호 변경",
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


@router.get(
    "/recommendations",
    summary="추천 요청 목록 조회",
    status_code=status.HTTP_200_OK,
    tags=["recommendations"],
)
def user_recommendations(
    user: User = Depends(only_self_access),
    user_recommendations: list[UserRecommendation] = Depends(get_current_user_recommendations),
) -> UserRecommendations:
    """추천 요청 목록 조회"""

    print("################### DEBUG: User Recommendations ###################")
    print("Received user recommendations request for user_id:", user.id)
    print("Retrieved user recommendations:", [x.recommendation_id for x in user_recommendations])
    print("################### DEBUG END: User Recommendations ###################")

    return {
        "total": 2,
        "items": [
            {
                "task_id": "unique_hash_value",
                "status": "completed",
                "region_id": 1,
                "name": "사용자 지정 추천 이름",
                "infrastructure_type_ids": [1, 2, 3],
                "sale_price": {
                    "min": 1,
                    "max": 1
                },
                "deposit_price": {
                    "min": 1,
                    "max": 1
                },
            },
            {
                "task_id": "unique_hash_value",
                "status": "in_progress",
                "region_id": 1,
                "name": None,
                "infrastructure_type_ids": [1, 2, 3],
                "sale_price": {
                    "min": 1,
                    "max": 1
                },
                "deposit_price": {
                    "min": 1,
                    "max": 1
                },
            },
        ],
    }
