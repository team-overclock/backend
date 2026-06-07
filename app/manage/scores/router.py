"""관리용 라우터"""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import PropertyInfrastructure
from ..schemas import ImmediateResponse, BackgroundSuccessResponse, ScoresStatusResponse

from .insert import run as insert


router = APIRouter(prefix="/data/scores")


@router.post(
    "",
    summary="점수 데이터 생성",
    status_code=status.HTTP_202_ACCEPTED,
)
def insert_scores(
    background_tasks: BackgroundTasks,
) -> BackgroundSuccessResponse:
    """
    Property-Infrastructure간 점수 데이터 생성 작업을 백그라운드에서 실행
    RADIUS_METERS 미터 반경 내 인프라에 대해 점수 계산 및 매핑 테이블에 저장
    """

    background_tasks.add_task(
        insert,
        silent=False,
    )

    return {
        "requested": True,
    }

@router.delete(
    "",
    summary="점수 데이터 삭제",
    status_code=status.HTTP_200_OK,
)
def delete_scores(
    db: Session = Depends(get_db),
) -> ImmediateResponse:
    """Property-Infrastructure간 점수 데이터 전체 삭제"""

    db.query(PropertyInfrastructure).delete()
    db.commit()

    return {
        "success": True,
    }

@router.get(
    "/status",
    summary="점수 데이터 개수 조회",
    status_code=status.HTTP_200_OK,
)
def get_score_status(
    db: Session = Depends(get_db),
) -> ScoresStatusResponse:
    """점수 데이터 총 개수 조회"""
    
    total = db.query(PropertyInfrastructure).count()

    return {
        "total": total,
    }
