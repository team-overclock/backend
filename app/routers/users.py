"""사용자 엔드포인트 라우트 모듈."""

from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..models import User, SearchLog
from ..database import get_db
from ..redis import get_redis
from ..core.enums import AppErrorCodeEnum, SchoolDistrictTypeEnum, InfrastructureTypeEnum
from ..core.exception import AppException
from ..crud.service import get_high_schools
from ..schemas.error import IncorrectCurrentPasswordError
from ..schemas.user import UserInfoUpdateRequest, UserInfo, UserPasswordChangeRequest
from ..schemas.service import UserRecommendations
from ..dependencies import only_self_access, get_current_user_recommendations

router = APIRouter(
    prefix="/users/me",
    tags=["users"],
)


@router.get(
    "",
    summary="사용자 정보 조회",
    status_code=status.HTTP_200_OK,
)
def user_info(
    user: User = Depends(only_self_access),
) -> UserInfo:
    """사용자 정보 조회"""
    return user


@router.patch(
    "",
    summary="사용자 정보 수정",
    status_code=status.HTTP_200_OK,
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

    db.commit()
    db.refresh(user)
    return user



@router.post(
    "/password",
    summary="비밀번호 변경",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: { "model": IncorrectCurrentPasswordError, "description": "현재 비밀번호가 일치하지 않는 경우" },
    }
)
def user_password_change(
    body: UserPasswordChangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
):
    """비밀번호 변경"""
    if not body.current_password or not user.verify_password(body.current_password):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=AppErrorCodeEnum.INCORRECT_CURRENT_PASSWORD,
            message="현재 비밀번호가 일치하지 않습니다.",
        )
    if body.new_password != body.current_password:
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
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
    user: User = Depends(only_self_access),
    user_recommendations: list[SearchLog] = Depends(get_current_user_recommendations),
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
                "requested_at": datetime.now(),
                "last_viewed_at": datetime.now(),
                "task_id": "unique_task_id",
                "status": "completed",
                "request_data": {
                    "name": "사용자 지정 추천 이름",
                    "region": {
                        "id": 1,
                        "name": "서울특별시 용산구 도원동"
                    },
                    "infrastructure_types": [
                        InfrastructureTypeEnum.SUBWAY_STATION.meta,
                    ],
                    "high_schools": [
                        get_high_schools(redis)[0],
                    ],
                    "school_districts": [
                        SchoolDistrictTypeEnum.INTENSIVE.meta,
                    ],
                    "sale_price": {
                        "min": 0,
                        "max": 999999999999,
                    },
                    "jeonse_price": {
                        "min": 0,
                        "max": 999999999999,
                    },
                },
            },
            {
                "requested_at": datetime.now(),
                "last_viewed_at": datetime.now(),
                "task_id": "unique_task_idw",
                "status": "in_progress",
                "request_data": {
                    "name": None,
                    "region": {
                        "id": 2,
                        "name": "서울특별시 용산구 새창로",
                    },
                    "infrastructure_types": [
                        InfrastructureTypeEnum.SUBWAY_STATION.meta,
                        InfrastructureTypeEnum.PARK.meta,
                    ],
                    "high_schools": [],
                    "school_districts": [
                        SchoolDistrictTypeEnum.INTENSIVE.meta,
                        SchoolDistrictTypeEnum.RELAXED.meta,
                    ],
                    "sale_price": {
                        "min": 0,
                        "max": 999999999999,
                    },
                    "jeonse_price": {
                        "min": 0,
                        "max": 999999999999,
                    },
                },
            },
        ],
    }
