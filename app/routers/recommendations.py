"""추천 엔드포인트 라우트 모듈."""

from typing import Union
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session

from ..redis import get_redis
from ..database import get_db
from ..core.enums import SchoolDistrictTypeEnum, InfrastructureTypeEnum
from ..core.validate import verify_region, verify_high_schools
from ..dependencies import only_self_access, get_current_recommendation, get_current_search_log
from ..models import User, SearchLog, Recommendation
from ..crud.service import get_high_schools
from ..schemas.error import RegionError
from ..schemas.common import TaskID, PK_AI
from ..schemas.service import (
    RecommendationCreateRequest,
    RecommendationCreateResponse,
    RecommendationReport,
    RecommendationMetadataUpdateRequest,
    RecommendationReportItemDetail,
)

from ..services.recommendation import generate_recommendation


router = APIRouter(prefix="/recommendations", tags=["recommendations"])
task_id_router = APIRouter(
    prefix="/{task_id}",
    responses={
        302: { "description": "task id가 full id가 아닌 경우" },
    }
)

# 유저별 추천 요청 목록은 user 라우터에 포함됨


@router.post(
    "",
    summary="추천 생성 요청",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: { "model": Union[RegionError], "description": "유효하지 않은 동네 및 인프라 유형이 포함되어 있는 경우" },
    }
)
def request_generate_recommendation(
    body: RecommendationCreateRequest,
    background_tasks: BackgroundTasks,
    redis = Depends(get_redis),
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
) -> RecommendationCreateResponse:
    """
    추천 요청을 받고 백그라운드에서 처리하도록 하는 엔드포인트.
    응답에 포함된 `task_id`로 추천 결과를 조회할 수 있음
    """

    region = verify_region(redis, body.region_id) if body.region_id else None
    schools = verify_high_schools(redis, body.high_school_ids) if body.high_school_ids else []

    rec_name = (body.name if body.name else "").strip() or None
    infrastructure_types = body.infrastructure_types
    school_district_types = body.school_district_types or []
    high_school_ids = [x["id"] for x in schools]
    sale_price_min = body.sale_price.min if body.sale_price else None
    sale_price_max = body.sale_price.max if body.sale_price else None
    jeonse_price_min = body.jeonse_price.min if body.jeonse_price else None
    jeonse_price_max = body.jeonse_price.max if body.jeonse_price else None

    task_id, _ = generate_recommendation(
        db,
        background_tasks,
        request_user=user,
        rec_name=rec_name,
        region=region,
        infrastructure_types=infrastructure_types,
        school_district_types=school_district_types,
        high_school_ids=high_school_ids,
        sale_price_min=sale_price_min,
        sale_price_max=sale_price_max,
        jeonse_price_min=jeonse_price_min,
        jeonse_price_max=jeonse_price_max,
    )

    return {
        "task_id": task_id,
    }


@task_id_router.patch(
    "",
    summary="추천 이름 변경",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_recommendation_name(
    task_id: TaskID,
    body: RecommendationMetadataUpdateRequest,
    db: Session = Depends(get_db),
    search_log: SearchLog = Depends(get_current_search_log),
):
    if "name" in body.model_dump(exclude_unset=True):
        search_log.name = body.name or None
    db.commit()
    return


@task_id_router.get(
    "",
    summary="추천 결과 요약 정보 조회",
    status_code=status.HTTP_200_OK,
)
def get_recommendation_summary(
    task_id: TaskID,
    recommendation: Recommendation = Depends(get_current_recommendation),
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
) -> RecommendationReport:
    """추천 결과 요약 정보 조회"""

    print("################### DEBUG: Get Recommendation ###################")
    print("task_id:", task_id)
    print("추천 정보:", recommendation)
    print("################### DEBUG END: Get Recommendation ###################")

    return {
        "task_id": "full_task_id",
        "status": "completed",
        "total": 2,
        "request_data": {
            "name": "this is custom name",
            "region": {
                "id": 1,
                "name": "서울특별시 용산구 도원동",
            },
            "infrastructure_types": [
                InfrastructureTypeEnum.SUBWAY_STATION.meta,
                InfrastructureTypeEnum.PARK.meta,
            ],
            "high_schools": get_high_schools(redis)[0:3],
            "school_districts": [
                SchoolDistrictTypeEnum.INTENSIVE.meta,
                SchoolDistrictTypeEnum.BALANCED.meta,
            ],
            "sale_price": {
                "min": 0,
                "max": 999999999999,
            },
            "jeonse_price": {
                "min": 0,
                "max": 999999999999,
            },
        },
        "properties": [
            {
                "id": 1,
                "name": "삼성래미안",
                "score": 87,
                "region": {
                    "id": 1,
                    "name": "서울특별시 용산구 도원동",
                },
                "address": {
                    "land_lot": "서울특별시 용산구 도원동 23",
                    "road_name": "서울특별시 용산구 새창로 70",
                    "latitude": 37.53830000,
                    "longitude": 126.95532000,
                },
                "sale_price": 1200000000,
                "jeonse_price": 440000000,
                "infrastructure": [
                    {
                        **InfrastructureTypeEnum.SUBWAY_STATION.meta._asdict(),
                        "distance": 0.6,
                        "walking_duration": 13,
                    },
                    {
                        **InfrastructureTypeEnum.PARK.meta._asdict(),
                        "distance": 1.5,
                        "walking_duration": 21,
                    },
                ],
            },
            {
                "id": 2,
                "name": "도원",
                "score": 79.3,
                "region": {
                    "id": 1,
                    "name": "서울특별시 용산구 도원동",
                },
                "address": {
                    "land_lot": "서울특별시 용산구 도원동 3-7",
                    "road_name": "서울특별시 용산구 새창로12길 11-15",
                    "latitude": 37.53895000,
                    "longitude": 126.95842000,
                },
                "sale_price": None,
                "jeonse_price": 150000000,
                "infrastructure": [
                    {
                        **InfrastructureTypeEnum.SUBWAY_STATION.meta._asdict(),
                        "distance": 1.3,
                        "walking_duration": 18,
                    },
                    {
                        **InfrastructureTypeEnum.PARK.meta._asdict(),
                        "distance": 1.1,
                        "walking_duration": 15,
                    },
                ],
            },
        ],
    }


@task_id_router.get(
    "/properties/{property_id}",
    summary="추천 매물의 상세 정보 조회",
    status_code=status.HTTP_200_OK,
)
def get_recommendation_property_detail(
    task_id: TaskID,
    property_id: PK_AI,
    db: Session = Depends(get_db),
    recommendation: Recommendation = Depends(get_current_recommendation),
) -> RecommendationReportItemDetail:
    """추천 결과 중 특정 매물의 상세 정보 조회"""

    print("################### DEBUG: Get Recommendation ###################")
    properties = recommendation.top_properties
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
        "region": {
            "id": 1,
            "name": "서울특별시 용산구 도원동",
        },
        "address": {
            "land_lot": "서울특별시 용산구 도원동 23",
            "road_name": "서울특별시 용산구 새창로 70",
            "latitude": 37.53830000,
            "longitude": 126.95532000,
        },
        "sale_price": 1200000000,
        "jeonse_price": 440000000,
        "infrastructure": [
            {
                **InfrastructureTypeEnum.SUBWAY_STATION.meta._asdict(),
                "name": "효창공원앞",
                "score": 93.3,
                "distance": 0.6,
                "walking_duration": 13,
                "latitude": 37.53895534,
                "longitude": 126.96173072,
            },
            {
                **InfrastructureTypeEnum.PARK.meta._asdict(),
                "name": "효창근린공원",
                "score": 57.8,
                "distance": 1.5,
                "walking_duration": 21,
                "latitude": 37.54523000,
                "longitude": 126.95993000,
            },
        ],
    }


router.include_router(task_id_router)
