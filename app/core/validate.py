from redis import Redis
from fastapi import status

from ..crud.service import get_region_by_id, get_regions, get_high_school_map
from ..schemas.service import RecommendationCreateRequest
from ..core.enums import (
    AppErrorCodeEnum,
    InfrastructureTypeEnum,
)
from ..core.exception import AppException


def verify_region(redis: Redis, region_id: int):
    """주어진 region_id가 유효한지 검증하는 함수. 유효하지 않으면 AppException을 발생시킴."""

    region = get_region_by_id(redis, region_id)
    if not region:
        regions = get_regions(redis)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=AppErrorCodeEnum.REGION_ERROR,
            message="유효하지 않은 동네입니다.",
            detail={
                "total": len(regions),
                "items": regions,
            },
        )
    return region


def verify_high_schools(redis: Redis, high_school_ids: list[int]) -> list[dict]:
    """
    주어진 고등학교 ID 목록이 유효한지 검증하는 함수.
    유효하지 않은 ID가 있으면 AppException을 발생시킴.
    """
    if not high_school_ids:
        return []

    unique_ids = list(set(high_school_ids))
    high_schools = get_high_school_map(redis)

    schools = []
    invalid_ids = []

    for school_id in unique_ids:
        school = high_schools.get(school_id)
        if school:
            schools.append(school)
        else:
            invalid_ids.append(school_id)

    if invalid_ids:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=AppErrorCodeEnum.HIGH_SCHOOL_ERROR,
            message="유효하지 않은 고등학교 ID가 포함되어 있습니다.",
            detail={
                "invalid_ids": invalid_ids,
            },
        )
    return schools


def verify_recommendation_request_data(
    redis: Redis,
    body: RecommendationCreateRequest,
):
    region = verify_region(redis, body.region_id) if body.region_id else {}

    return {
        "region_id": region.get("id"),
        "region_name": region.get("name"),
        "infrastructure_types": body.infrastructure_types,
        # 학군 유형은 인프라 유형 내 초/중/고등학교 중 1개 이상 포함된 경우에만 사용
        "school_district_types": body.school_district_types if any([x in (InfrastructureTypeEnum.ELEMENTARY_SCHOOL, InfrastructureTypeEnum.MIDDLE_SCHOOL, InfrastructureTypeEnum.HIGH_SCHOOL) for x in body.infrastructure_types]) else [],
        # 고등학교 목록은 인프라 유형 내 고등학교가 포함된 경우에만 사용
        "high_school_ids": [s["id"] for s in verify_high_schools(redis, body.high_school_ids)] if body.high_school_ids and InfrastructureTypeEnum.HIGH_SCHOOL in body.infrastructure_types else [],
        "sale_price_min": body.sale_price.min if body.sale_price else None,
        "sale_price_max": body.sale_price.max if body.sale_price else None,
        "jeonse_price_min": body.jeonse_price.min if body.jeonse_price else None,
        "jeonse_price_max": body.jeonse_price.max if body.jeonse_price else None,
    }
