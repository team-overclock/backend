"""누구나 접근 가능한 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends

from ..redis import get_redis
from ..schemas.service import HighSchoolsResponse
from ..crud.service import (
    get_high_schools,
)


router = APIRouter(
    prefix="/infrastructures",
    tags=["infrastructures"],
)


@router.get(
    "/high-schools",
    summary="고등학교 목록 조회",
)
def get_high_schools_list(
    redis = Depends(get_redis),
) -> HighSchoolsResponse:
    """고등학교 목록 반환"""
    items = get_high_schools(redis)
    return {
        "total": len(items),
        "items": items,
    }
