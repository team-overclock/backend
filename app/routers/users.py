"""사용자 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..models import User, SearchLog
from ..database import get_db
from ..redis import get_redis
from ..core.enums import AppErrorCodeEnum, SchoolDistrictTypeEnum, InfrastructureTypeEnum
from ..core.exception import AppException
from ..crud.service import get_high_school_map, get_region_by_name
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

    high_schools = get_high_school_map(redis)
    items = []
    for search_log in user_recommendations:
        recommendation = search_log.recommendation
        items.append({
            "task_id": search_log.task_id,
            "status": "in_progress" if recommendation.in_progress else "completed",
            "requested_at": search_log.requested_at,
            "last_viewed_at": search_log.last_viewed_at,
            "request_data": {
                "name": search_log.name,
                "region": get_region_by_name(redis, recommendation.region) if recommendation.region else None,
                "infrastructure_types": [InfrastructureTypeEnum[x].meta for x in recommendation.infrastructure_priorities],
                "high_schools": [high_schools[x] for x in recommendation.high_school_ids if high_schools.get(x)],
                "school_districts": [SchoolDistrictTypeEnum[x].meta for x in recommendation.school_district_types],
                "sale_price": {
                    "min": recommendation.sale_price_min,
                    "max": recommendation.sale_price_max,
                },
                "jeonse_price": {
                    "min": recommendation.jeonse_price_min,
                    "max": recommendation.jeonse_price_max,
                },
            },
        })

    return {
        "total": len(items),
        "items": items,
    }
