"""추천 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.validate import verify_region, verify_infrastructure_types
from ..dependencies import only_self_access, get_current_recommendation, get_current_version
from ..models import Recommendation, Version
from ..crud.service import create_recommendation, get_recommendation_by_hash
from ..models import User
from ..schemas.error import AppError, RegionOrInfrastructureTypeError
from ..schemas.common import TaskID, PK_AI
from ..schemas.service import (
    RecommendationCreateRequest,
    RecommendationCreateResponse,
    RecommendationReport,
    RecommendationReportItemDetail,
)
from ..services.recommendation import generate_recommendation_task_id, generate_recommendation


router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# Recommendation 모델의 hash 값을 task_id로 사용
# 유저별 추천 요청 목록은 user 라우터에서 관리함


@router.post(
    "",
    summary="추천 생성 요청",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: { "model": RegionOrInfrastructureTypeError, "description": "유효하지 않은 동네 및 인프라 유형이 포함되어 있는 경우" },
    }
)
def request_generate_recommendation(
    body: RecommendationCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
    version: Version = Depends(get_current_version),
) -> RecommendationCreateResponse:
    """
    추천 요청을 받고 백그라운드에서 처리하도록 하는 엔드포인트.
    응답에 포함된 `task_id`로 추천 결과를 조회할 수 있음
    """

    region = verify_region(db, body.region_id)
    infras = verify_infrastructure_types(db, body.infrastructure_type_ids)
    sale_price_min = body.sale_price.min if body.sale_price else None,
    sale_price_max = body.sale_price.max if body.sale_price else None,
    deposit_price_min = body.deposit_price.min if body.deposit_price else None,
    deposit_price_max = body.deposit_price.max if body.deposit_price else None,

    status_code = "in_progress"
    task_id = generate_recommendation_task_id(region.id, [i.id for i in infras], sale_price_min, sale_price_max, deposit_price_min, deposit_price_max)
    recommendation = get_recommendation_by_hash(db, task_id)
    if recommendation:
        if recommendation.finished_at:
            status_code = "completed"
        elif recommendation.failed_at:
            recommendation.failed_at = None

    if status_code == "in_progress":
        if not recommendation:
            recommendation = create_recommendation(
                db,
                task_id=task_id,
                region=region,
                sale_price_min=sale_price_min,
                sale_price_max=sale_price_max,
                deposit_price_min=deposit_price_min,
                deposit_price_max=deposit_price_max,
                version=version,
                infrastructure_types=infras,
            )
        recommendation.add_user(user, body.name)
        recommendation.version = version
        db.commit()

        # 백그라운드에서 비동기로 추천 생성 실행
        background_tasks.add_task(
            generate_recommendation,
            task_id=task_id,
        )

    return {
        "task_id": task_id,
        "status": status_code,
    }


@router.get(
    "/{task_id}",
    summary="추천 결과 요약 정보 조회",
    status_code=status.HTTP_200_OK,
    responses={
        400: { "model": AppError, "description": "`task_id` 값이 유효하지 않은 경우" },
    }
)
def get_recommendation_summary(
    task_id: TaskID,
    recommendation: Recommendation = Depends(get_current_recommendation),
) -> RecommendationReport:
    """추천 결과 요약 정보 조회"""

    print("################### DEBUG: Get Recommendation ###################")
    print("task_id:", task_id)
    print("추천 정보:", recommendation)
    print("################### DEBUG END: Get Recommendation ###################")

    return {
        "task_id": "full_hash_value",
        "status": "completed",
        "total": 2,
        "request_data": {
            "name": "string",
            "region": "서울특별시 용산구 도원동",
            "infrastructure_types": [
                "지하철역",
                "공원·녹지",
            ],
            "sale_price": {
                "min": 0,
                "max": 999999999999,
            },
            "deposit_price": {
                "min": 0,
                "max": 999999999999,
            },
        },
        "properties": [
            {
                "id": 1,
                "name": "삼성래미안",
                "score": 87,
                "address": {
                    "land_lot": "서울특별시 용산구 도원동 23",
                    "road_name": "서울특별시 용산구 새창로 70",
                    "latitude": 37.53830000,
                    "longitude": 126.95532000,
                },
                "sale_price": 1200000000,
                "deposit_price": 440000000,
                "infrastructure": [
                    {
                        "type": "지하철역",
                        "distance": 0.6,
                        "walking_duration": 13,
                    },
                    {
                        "type": "공원·녹지",
                        "distance": 1.5,
                        "walking_duration": 21,
                    },
                ],
            },
            {
                "id": 2,
                "name": "도원",
                "score": 79.3,
                "address": {
                    "land_lot": "서울특별시 용산구 도원동 3-7",
                    "road_name": "서울특별시 용산구 새창로12길 11-15",
                    "latitude": 37.53895000,
                    "longitude": 126.95842000,
                },
                "sale_price": None,
                "deposit_price": 150000000,
                "infrastructure": [
                    {
                        "type": "지하철역",
                        "distance": 1.3,
                        "walking_duration": 18,
                    },
                    {
                        "type": "공원·녹지",
                        "distance": 1.1,
                        "walking_duration": 15,
                    },
                ],
            },
        ],
    }


@router.get(
    "/{task_id}/properties/{property_id}",
    summary="추천 매물의 상세 정보 조회",
    status_code=status.HTTP_200_OK,
    responses={
        400: { "model": AppError, "description": "`task_id` 값이 유효하지 않은 경우" },
    }
)
def get_recommendation_property_detail(
    task_id: TaskID,
    property_id: PK_AI,
    recommendation: Recommendation = Depends(get_current_recommendation),
) -> RecommendationReportItemDetail:
    """추천 결과 중 특정 매물의 상세 정보 조회"""

    print("################### DEBUG: Get Recommendation ###################")
    properties = [x for x in recommendation.property_scores if x.property_id == property_id]
    property = properties[0] if len(properties) > 0 else None
    print("task_id:", task_id)
    print("property_id:", property_id)
    print("추천 정보:", recommendation)
    print("매물 정보:", property)
    print("################### DEBUG END: Get Recommendation ###################")

    return {
        "id": 1,
        "name": "삼성래미안",
        "score": 87,
        "address": {
            "land_lot": "서울특별시 용산구 도원동 23",
            "road_name": "서울특별시 용산구 새창로 70",
            "latitude": 37.53830000,
            "longitude": 126.95532000,
        },
        "sale_price": 1200000000,
        "deposit_price": 440000000,
        "infrastructure": [
            {
                "type": "지하철역",
                "name": "효창공원앞",
                "score": 93.3,
                "distance": 0.6,
                "walking_duration": 13,
                "latitude": 37.53895534,
                "longitude": 126.96173072,
            },
            {
                "type": "공원·녹지",
                "name": "효창근린공원",
                "score": 57.8,
                "distance": 1.5,
                "walking_duration": 21,
                "latitude": 37.54523000,
                "longitude": 126.95993000,
            },
        ],
    }
