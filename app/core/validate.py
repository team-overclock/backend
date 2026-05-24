from redis import Redis
from fastapi import status

from ..crud.service import get_region_by_id, get_regions
from ..core.enums import AppErrorCodeEnum, INFRASTRUCTURE_TYPE_MAP, INFRASTRUCTURE_TYPES
from ..core.exception import AppException
from ..schemas.service import InfrastructureTypeItem


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

def verify_infrastructure_type(infrastructure_type: int):
    """주어진 infrastructure_type_id가 유효한지 검증하는 함수. 유효하지 않으면 AppException을 발생시킴."""

    if infrastructure_type not in INFRASTRUCTURE_TYPES:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=AppErrorCodeEnum.INFRASTRUCTURE_TYPE_ERROR,
            message="유효하지 않은 인프라 유형입니다.",
            detail={
                "total": len(INFRASTRUCTURE_TYPES),
                "items": INFRASTRUCTURE_TYPES,
            },
        )
    return INFRASTRUCTURE_TYPES[infrastructure_type]

def verify_infrastructure_types(infrastructure_types: list[str]) -> list[InfrastructureTypeItem]:
    """
    주어진 인프라 유형 ID 목록의 중복을 제거한 후 모든 id가 유효한지 검증하는 함수.
    유효하지 않은 값이 하나라도 포함되어 있으면 AppException을 발생시킴.
    """
    if len(infrastructure_types) == 0:
        return []

    types = list(dict.fromkeys(infrastructure_types))  # 순서를 유지한 채로 중복 제거
    try:
        infras = [INFRASTRUCTURE_TYPE_MAP[x] for x in types]
        if len(infras) != len(types): raise
    except:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=AppErrorCodeEnum.INFRASTRUCTURE_TYPE_ERROR,
            message="유효하지 않은 인프라 유형이 포함되어 있습니다.",
            detail={
                "total": len(INFRASTRUCTURE_TYPES),
                "items": INFRASTRUCTURE_TYPES,
            },
        )
    return infras
