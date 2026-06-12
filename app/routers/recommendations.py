"""추천 엔드포인트 라우트 모듈."""

from typing import Union
from fastapi import APIRouter, Depends, BackgroundTasks, Request, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from ..redis import get_redis
from ..database import get_db
from ..core.enums import SchoolDistrictTypeEnum, InfrastructureTypeEnum
from ..core.validate import verify_region, verify_high_schools
from ..dependencies import only_self_access, get_current_search_log
from ..models import User, SearchLog, Property, Infrastructure
from ..crud.service import get_high_school_map, get_region_by_name
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

    rec_name = (body.name if body.name else "").strip() or None
    rec = generate_recommendation(
        db,
        redis,
        background_tasks,
        request_user=user,
        rec_name=rec_name,
        request_data=body,
    )

    return {
        "task_id": rec.task_id,
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
    search_log: SearchLog = Depends(get_current_search_log),
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
) -> RecommendationReport:
    """추천 결과 요약 정보 조회"""

    recommendation = search_log.recommendation
    high_schools = get_high_school_map(redis)

    in_progress = recommendation.in_progress
    top_properties = recommendation.top_properties
    request_data = {
        "name": search_log.name,
        "region": get_region_by_name(redis, recommendation.region) if recommendation.region else None,
        "infrastructure_types": [InfrastructureTypeEnum[x].meta for x in recommendation.infrastructure_priorities],
        "high_schools": [high_schools[x] for x in recommendation.high_school_ids if high_schools.get(x)],
        "school_districts": [SchoolDistrictTypeEnum[x].meta for x in recommendation.school_district_types],
        "sale_price": {
            "min": recommendation.sale_price_min,
            "max": recommendation.sale_price_max,
        },
        "jeonse_price": {
            "min": recommendation.jeonse_price_min,
            "max": recommendation.jeonse_price_max,
        },
    }

    db_properties = db.query(Property).filter(Property.id.in_([p["id"] for p in top_properties])).all()
    property_map = {prop.id: prop for prop in db_properties}

    properties = [
        {
            **p,
            "region": get_region_by_name(redis, p["region"]),
            "address": {
                "land_lot": property_map[p["id"]].land_lot_address,
                "road_name": property_map[p["id"]].road_name_address,
                "latitude": property_map[p["id"]].latitude,
                "longitude": property_map[p["id"]].longitude,
            },
            "sale_price": {
                "min": p["sale_price_min"],
                "max": p["sale_price_max"],
            },
            "jeonse_price": {
                "min": p["jeonse_price_min"],
                "max": p["jeonse_price_max"],
            },
            "infrastructure": [
                {
                    **InfrastructureTypeEnum[infra["type"]].meta._asdict(),
                    **infra,
                } for infra in p["infrastructure_scores"][:2]
            ],
        } for p in top_properties
    ]

    return {
        "task_id": task_id,
        "status": "in_progress" if in_progress else "completed",
        "total": len(properties),
        "request_data": request_data,
        "properties": properties,
    }


@task_id_router.get(
    "/properties/{property_id}",
    summary="추천 매물의 상세 정보 조회",
    status_code=status.HTTP_200_OK,
)
def get_recommendation_property_detail(
    task_id: TaskID,
    property_id: PK_AI,
    request: Request,
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
    user: User = Depends(only_self_access),
    search_log: SearchLog = Depends(get_current_search_log),
) -> RecommendationReportItemDetail:
    """추천 결과 중 특정 매물의 상세 정보 조회"""

    recommendation = search_log.recommendation

    search_log = get_current_search_log(task_id, request, db, user)
    ids = [x["id"] for x in search_log.recommendation.top_properties]
    if property_id not in ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )

    db_property = db.query(Property).filter(Property.id == property_id).first()
    top_property_map = {prop["id"]: prop for prop in recommendation.top_properties}
    info = top_property_map[property_id]

    db_infras = db.query(Infrastructure).filter(Infrastructure.id.in_([i["id"] for i in info["infrastructure_scores"]])).all()
    infra_map = {infra.id: infra for infra in db_infras}
    infrastructure = [
        {
            **InfrastructureTypeEnum[infra["type"]].meta._asdict(),
            **infra,
            "latitude": infra_map[infra["id"]].latitude,
            "longitude": infra_map[infra["id"]].longitude,
        } for infra in info["infrastructure_scores"]
    ]

    return {
        "id": info["id"],
        "name": info["name"],
        "score": info["score"],
        "region": get_region_by_name(redis, info["region"]),
        "address": {
            "land_lot": db_property.land_lot_address,
            "road_name": db_property.road_name_address,
            "latitude": db_property.latitude,
            "longitude": db_property.longitude,
        },
        "sale_price": {
            "min": info["sale_price_min"],
            "max": info["sale_price_max"],
        },
        "jeonse_price": {
            "min": info["jeonse_price_min"],
            "max": info["jeonse_price_max"],
        },
        "infrastructure": infrastructure,
    }


router.include_router(task_id_router)
