from fastapi import status
from sqlalchemy.orm import Session

from ..crud import get_regions_by_depth, get_regions_by_full_name
from ..core.exception import AppException


def verify_region(db: Session, full_name: str, depth: int = 2):
    """주어진 region이 유효한지 검증하는 함수. 유효하지 않으면 AppException을 발생시킴."""
    region = get_regions_by_full_name(db, full_name, depth)
    if not region:
        _, region_names = get_regions_by_depth(db, depth)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="유효하지 않은 동네입니다.",
            detail={
                "total": len(region_names),
                "items": region_names,
            },
        )
    return region
