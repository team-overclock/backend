"""추천 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.validate import verify_region, verify_infrastructure_types
from ..dependencies import only_self_access, get_current_recommendation
from ..models import Recommendation
from ..models import User
from ..schemas.error import AppError, RegionOrInfrastructureTypeError
from ..schemas.service import (
    TaskID,
    CreateRecommendationRequest,
    CreateRecommendationResponse,
    RecommendationDetailResponse,
)


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
def create_recommendation(
    body: CreateRecommendationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
) -> CreateRecommendationResponse:
    """
    추천 요청을 받고 백그라운드에서 처리하도록 하는 엔드포인트.
    응답에 포함된 `task_id`로 추천 결과를 조회할 수 있음
    """

    region = verify_region(db, body.region_id)
    infras = verify_infrastructure_types(db, body.infrastructure_type_ids)
    if not region or not len(infras) == 0:
        pass

    print("################### DEBUG: Create Recommendation Request ###################")
    print("Received recommendation request:", body)
    print("region", region.to_dict() if region else None)
    print("infras", [i.to_dict() for i in infras])
    print("sale_price", body.sale_price)
    print("deposit_price", body.deposit_price)
    print("################### DEBUG END: Create Recommendation Request ###################")

    # 입력받은 조건들을 기반으로 hash(task_id) 생성
    hash = "unique_hash_value"

    # 추천 로직 백그라운드로 실행
    # 해당 hash 값이 이미 존재한다면(이미 같은 조건으로 추천한 적이 있다면) 추천 로직을 수행할 필요 없음

    return {"task_id": hash}


@router.get(
    "/{task_id}",
    summary="추천 결과 조회",
    status_code=status.HTTP_200_OK,
    responses={
        400: { "model": AppError, "description": "`task_id` 값이 유효하지 않은 경우" },
    }
)
def get_recommendation(
    task_id: TaskID,
    recommendation: Recommendation = Depends(get_current_recommendation),
) -> RecommendationDetailResponse:
    """추천 결과 조회"""

    print("################### DEBUG: Get Recommendation ###################")
    print("task_id에 해당하는 검증이 완료된 추천:", recommendation)
    print("################### DEBUG END: Get Recommendation ###################")

    return {
        "status": "completed",
        "total": 1,
        "items": [
            {
                "name": "삼성래미안",
                "score": 87,
                "address": {
                    "land_lot": "서울특별시 용산구 도원동 23",
                    "road_name": "서울특별시 용산구 새창로 70",
                    "latitude": 37.53830000,
                    "longitude": 126.95532000,
                },
                "sale_price": {
                    "min": 1200000000,
                    "max": 1700000000,
                },
                "deposit_price": {
                    "min": 440000000,
                    "max": 750000000,
                },
                "infrastructure": [
                    {
                        "type_id": 5,
                        "type_name": "지하철역",
                        "name": "효창공원앞",
                        "score": 93.3,
                        "distance": 0.6,
                        "walking_duration": 13,
                        "latitude": 37.53895534,
                        "longitude": 126.96173072,
                    },
                    {
                        "type_id": 2,
                        "type_name": "공원·녹지",
                        "name": "효창근린공원",
                        "score": 57.8,
                        "distance": 1.5,
                        "walking_duration": 21,
                        "latitude": 37.54523000,
                        "longitude": 126.95993000,
                    },
                ],
            },
            {
                "name": "도원",
                "score": 79.3,
                "address": {
                    "land_lot": "서울특별시 용산구 도원동 3-7",
                    "road_name": "서울특별시 용산구 새창로12길 11-15",
                    "latitude": 37.53895000,
                    "longitude": 126.95842000,
                },
                "sale_price": None,
                "deposit_price": {
                    "min": 150000000,
                    "max": 150000000,
                },
                "infrastructure": [
                    {
                        "type_id": 5,
                        "type_name": "지하철역",
                        "name": "효창공원앞",
                        "score": 76.5,
                        "distance": 1.3,
                        "walking_duration": 18,
                        "latitude": 37.53895534,
                        "longitude": 126.96173072,
                    },
                    {
                        "type_id": 2,
                        "type_name": "공원·녹지",
                        "name": "효창근린공원",
                        "score": 86.6,
                        "distance": 1.1,
                        "walking_duration": 15,
                        "latitude": 37.54523000,
                        "longitude": 126.95993000,
                    },
                ],
            },
        ],
    }
