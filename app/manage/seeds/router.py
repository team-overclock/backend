"""시드 데이터 관련 API 라우터"""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import union_all, select, func
from sqlalchemy.orm import Session

from ...config import SEED_USERNAME_PREFIX, SEED_TASK_ID_PREFIX
from ...database import get_db
from ...models import User, Recommendation

from ..schemas import ImmediateResponse, BackgroundSuccessResponse, GenerateSeedsRequest, SeedsStatusResponse
from .insert import run as insert_seeds
from .drop import run as drop_seeds



router = APIRouter(prefix="/seeds")

@router.post(
    "",
    summary="시드 데이터 생성",
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_seeds(
    body: GenerateSeedsRequest,
    background_tasks: BackgroundTasks,
) -> BackgroundSuccessResponse:
    """랜덤 시드 데이터 생성"""

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
    status_code=status.HTTP_200_OK,
)
def delete_seeds(
) -> ImmediateResponse:
    """
    랜덤 시드 데이터 삭제.
    단, property-infra 사이 점수 등 데이터는 삭제되지 않음.
    """

    try:
        drop_seeds()
        success = True
    except:
        success = False

    return {
        "success": success,
    }

@router.get(
    "/status",
    summary="시드 데이터 개수 조회",
    status_code=status.HTTP_200_OK,
)
def check_seed_status(
    db: Session = Depends(get_db),
) -> SeedsStatusResponse:
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
