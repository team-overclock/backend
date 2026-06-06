"""누구나 접근 가능한 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends

from ..redis import get_redis
from ..core.enums import INFRASTRUCTURE_TYPES, SCHOOL_DISTRICT_TYPES
from ..schemas.service import RegionsResponse, InfrastructureTypesResponse, SchoolDistrictsResponse
from ..crud.service import get_regions as get_all_regions


router = APIRouter(
    tags=["public"],
)


@router.get(
    "/regions",
    summary="동네 목록 조회",
)
def get_regions(
    redis = Depends(get_redis),
) -> RegionsResponse:
    """regions 목록 반환"""
    items = get_all_regions(redis)
    return {
        "total": len(items),
        "items": items,
    }


@router.get(
    "/infrastructure-types",
    summary="인프라 유형 목록 조회",
)
def get_infrastructure_types(
) -> InfrastructureTypesResponse:
    """인프라 유형 목록 반환"""
    return {
        "total": len(INFRASTRUCTURE_TYPES),
        "items": INFRASTRUCTURE_TYPES,
    }


@router.get(
    "/school-districts-types",
    summary="학군 유형 목록 조회",
)
def get_school_districts(
) -> SchoolDistrictsResponse:
    """학군 유형 목록 반환"""
    return {
        "total": len(SCHOOL_DISTRICT_TYPES),
        "items": SCHOOL_DISTRICT_TYPES,
    }
