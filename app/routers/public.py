"""누구나 접근 가능한 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.service import RegionsResponse, InfrastructureTypesResponse
from ..crud import get_regions_by_depth, get_all_infrastructure_types


router = APIRouter(
    tags=["public"],
)


@router.get("/regions")
def get_regions(
    db: Session = Depends(get_db),
) -> RegionsResponse:
    """regions 목록 반환"""
    items = get_regions_by_depth(db, 2)
    return {
        "total": len(items),
        "items": [r.to_dict() for r in items],
    }


@router.get("/infrastructure-types")
def get_infrastructure_types(
    db: Session = Depends(get_db),
) -> InfrastructureTypesResponse:
    """인프라 유형 목록 반환"""
    items = get_all_infrastructure_types(db)
    return {
        "total": len(items),
        "items": items,
    }
