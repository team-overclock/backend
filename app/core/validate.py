from fastapi import status
from sqlalchemy.orm import Session

from ..crud.service import get_regions_by_depth, get_region_by_id, get_all_infrastructure_types, get_infrastructure_by_id, get_infrastructure_by_ids, get_recommendation_by_hash_and_user_id
from ..core.exception import AppException
from ..models import InfrastructureType


def verify_region(db: Session, region_id: int, depth: int = 2):
    """주어진 region_id가 유효한지 검증하는 함수. 유효하지 않으면 AppException을 발생시킴."""

    region = get_region_by_id(db, region_id, depth)
    if not region:
        regions = get_regions_by_depth(db, depth)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="유효하지 않은 동네입니다.",
            detail={
                "total": len(regions),
                "items": [r.to_dict() for r in regions],
            },
        )
    return region

def verify_infrastructure_type(db: Session, infrastructure_type_id: int):
    """주어진 infrastructure_type_id가 유효한지 검증하는 함수. 유효하지 않으면 AppException을 발생시킴."""

    infra = get_infrastructure_by_id(db, infrastructure_type_id)
    if not infra:
        infras = get_all_infrastructure_types(db)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="유효하지 않은 인프라 유형입니다.",
            detail={
                "total": len(infras),
                "items": [i.to_dict() for i in infras],
            },
        )
    return infra

def verify_infrastructure_types(db: Session, infrastructure_type_ids: list[int]) -> list[InfrastructureType]:
    """
    주어진 인프라 유형 ID 목록의 중복을 제거한 후 모든 id가 유효한지 검증하는 함수.
    유효하지 않은 값이 하나라도 포함되어 있으면 AppException을 발생시킴.
    """
    if len(infrastructure_type_ids) == 0:
        return []

    ids = list(dict.fromkeys(infrastructure_type_ids))  # 순서를 유지한 채로 중복 제거
    infras = get_infrastructure_by_ids(db, ids)
    if len(infras) != len(ids):
        infras = get_all_infrastructure_types(db)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="유효하지 않은 인프라 유형이 포함되어 있습니다.",
            detail={
                "total": len(infras),
                "items": [i.to_dict() for i in infras],
            },
        )
    return infras

def verify_recommendation(db: Session, recommendation_hash: str | None, user_id: str | None):
    """주어진 추천 hash가 유효한지 검증하는 함수. 유효하지 않으면 AppException을 발생시킴."""
    if recommendation_hash is None or user_id is None:
        return None

    recommendation = get_recommendation_by_hash_and_user_id(db, recommendation_hash, user_id)
    if not recommendation:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="유효하지 않은 추천입니다.",
        )
    return recommendation
