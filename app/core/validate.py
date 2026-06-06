from redis import Redis
from fastapi import status

from ..crud.service import get_region_by_id, get_regions, get_high_school_map
from ..core.enums import (
    AppErrorCodeEnum,
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
