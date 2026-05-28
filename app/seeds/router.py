"""개발용"""

from typing import Literal
from pydantic import BaseModel, Field
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import select, func, union_all
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Recommendation

from ..config import SEED_USERNAME_PREFIX, SEED_TASK_ID_PREFIX
from .insert import run as insert_seeds
from .drop import run as drop_seeds


class GenerateSeedsRequest(BaseModel):
    """시드 데이터 생성 요청"""

    users: int = Field(0, description="생성할 사용자 수")
    recommendations: int = Field(0, description="생성할 추천 수")

class SeedsResponse(BaseModel):
    """시드 데이터 생성/삭제 응답"""

    requested: Literal[True]

class GetSeedsResponse(BaseModel):
    """시드 데이터 개수 조회 응답"""

    total_users: int
    total_recommendations: int


router = APIRouter(prefix="/seeds", tags=["seeds"])

@router.post(
    "",
    summary="시드 데이터 생성",
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_seeds(
    body: GenerateSeedsRequest,
    background_tasks: BackgroundTasks,
) -> SeedsResponse:
    """랜덤 시드 데이터 생성"""

    # 백그라운드로 생성 및 즉시 응답
    background_tasks.add_task(
        insert_seeds,
        num_recommendations=body.recommendations,
        num_users=body.users,
        silent=True,
    )

    return {
        "requested": True,
    }

@router.delete(
    "",
    summary="시드 데이터 삭제",
    status_code=status.HTTP_202_ACCEPTED,
)
def delete_seeds(
    background_tasks: BackgroundTasks,
) -> SeedsResponse:
    """
    랜덤 시드 데이터 삭제.
    단, property-infra 사이 점수 등 데이터는 삭제되지 않음.
    """

    # 백그라운드로 생성 및 즉시 응답
    background_tasks.add_task(
        drop_seeds,
    )

    return {
        "requested": True,
    }

@router.get(
    "/status",
    summary="시드 데이터 개수 조회",
    status_code=status.HTTP_200_OK,
)
def get_number_of_seeds(
    db: Session = Depends(get_db),
) -> GetSeedsResponse:
    """
    사용자 및 추천 시드 데이터 개수 조회
    (게스트 유저는 미포함, 게스트와 연결된 시드 데이터는 포함됨)
    """

    total_users, total_recs = db.execute(
        union_all(
            select(func.count(User.id)).filter(User.email.startswith(SEED_USERNAME_PREFIX)),
            select(func.count(Recommendation.id)).filter(Recommendation.task_id.startswith(SEED_TASK_ID_PREFIX)),
        )
    ).scalars().all()

    return {
        "total_users": total_users,
        "total_recommendations": total_recs,
    }
