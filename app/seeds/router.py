"""개발용"""

from typing import Literal
from pydantic import BaseModel, Field
from fastapi import APIRouter, BackgroundTasks, status

from .insert import run as insert_seeds
from .drop import run as drop_seeds


class GenerateSeedsRequest(BaseModel):
    """시드 데이터 생성 요청"""

    users: int = Field(0, description="생성할 사용자 수")
    recommendations: int = Field(0, description="생성할 추천 수")

class SeedsResponse(BaseModel):
    """시드 데이터 생성/삭제 응답"""

    requested: Literal[True]


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
