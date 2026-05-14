#!/usr/bin/with-contenv python3

import os
import sys
import random
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.demo import create_guest_user
from app.models import (
    User,
    Version,
    Region,
    Recommendation,
    RecommendationInfrastructureTypePriority,
    UserRecommendation,
    InfrastructureType,
    Infrastructure,
    Property,
    PropertyInfrastructureScore,
    RecommendationPropertyScore,
    RecommendationPropertyInfrastructureScore,
)

from scripts.common import run_with_progress


DEFAULT_NUM_RECOMMENDATIONS = 30

start_ts = int(datetime(2022, 1, 1, 0, 0, 0).timestamp())
end_ts = int(datetime(2026, 12, 31, 23, 59, 59).timestamp())


def usage():
    print(f"사용법: python insert_seeds.py [생성할 추천 수]")
    print(f"  - 데이터베이스 내 데이터를 기반으로 랜덤 추천 데이터를 생성하여 삽입합니다.")
    print(f"  - 생성할 추천 수 기본 값: {DEFAULT_NUM_RECOMMENDATIONS}")


def random_range(min_value: int, max_value: int):
    results = random.sample(range(min_value, max_value + 1), k=2)
    min, max = sorted(results)
    return min, max


def get_latest_version(db: Session):
    """데이터가 삽입되어 있는지 확인 및 최신 버전 반환"""
    version = db.query(Version).order_by(Version.registered_at.desc()).first()
    if version is None:
        raise Exception("데이터가 없습니다. 먼저 데이터를 삽입해 주세요.")
    return version

def get_or_create_guest_user(db: Session):
    """게스트 사용자 조회 및 생성"""
    return create_guest_user(db)[0]


def generate_seed(
    db: Session,
    suffix: str,
    user: User,
    regions: list[Region],
    infra_types: list[InfrastructureType],
    infras: list[Infrastructure],
    properties: list[Property],
    version: Version,
):
    selected_region = random.choice(regions)
    has_sale_price = random.choice([True, False])
    has_deposit_price = random.choice([True, False])
    selected_sale_price = random_range(0, 999999999999) if has_sale_price else (None, None)
    selected_deposit_price = random_range(0, 999999999999) if has_deposit_price else (None, None)
    created_at, finished_at = random_range(start_ts, end_ts)
    created_at = datetime.fromtimestamp(created_at)
    is_failed = random.choice([True] * 4 + [False])
    failed_at = (created_at + timedelta(minutes=random.randint(1, 1000))) if is_failed else None
    finished_at = datetime.fromtimestamp(finished_at) if not is_failed and random.choice([True, False]) else None
    rec = Recommendation(
        hash=f"seed_{suffix}",
        region=selected_region,
        sale_price_min=selected_sale_price[0],
        sale_price_max=selected_sale_price[1],
        deposit_price_min=selected_deposit_price[0],
        deposit_price_max=selected_deposit_price[1],
        created_at=created_at,
        finished_at=finished_at,
        updated_at=finished_at,
        failed_at=failed_at,
        version=version,
    )
    db.add(rec)

    is_last_viewed = random.choice([True, False])
    last_viewed_at = rec.created_at + timedelta(minutes=random.randint(1, 1000)) if is_last_viewed else None
    user_rec = UserRecommendation(user=user, recommendation=rec, requested_at=rec.created_at, last_viewed_at=last_viewed_at)
    db.add(user_rec)

    selected_infra_types = random.sample(infra_types, k=random.randint(1, len(infra_types)))
    rec_infra_priorities = [
        create_recommendation_infrastructure_type_priority(db, rec, selected_infra_type, idx + 1)
        for idx, selected_infra_type in enumerate(selected_infra_types)
    ]

    selected_properties = random.sample(properties, k=random.randint(5, 10))
    for curr_property in selected_properties:
        for rec_infra in rec_infra_priorities:
            infra = random.choice(list(filter(lambda x: x.type == rec_infra.infrastructure_type, infras)))
            create_property_infrastructure_score(db, curr_property, infra, random.uniform(0.01, 100.0), random.randint(10, 1000))
            create_recommendation_property_infrastructure_score(db, rec, curr_property, infra, random.uniform(0.01, 100.0))
        create_recommendation_property_score(db, rec, curr_property, random.uniform(0.01, 100.0))

    return rec

def create_recommendation_infrastructure_type_priority(
    db: Session,
    recommendation: Recommendation,
    infrastructure_type: list[InfrastructureType],
    priority: int,
):
    ins = RecommendationInfrastructureTypePriority(
        recommendation=recommendation,
        infrastructure_type=infrastructure_type,
        priority=priority,
    )
    db.add(ins)
    return ins

def create_property_infrastructure_score(
    db: Session,
    property: Property,
    infrastructure: Infrastructure,
    score: float,
    distance: int,
):
    walking_duration = distance // 80
    ins = db.query(PropertyInfrastructureScore).filter(
        PropertyInfrastructureScore.property_id == property.id,
        PropertyInfrastructureScore.infrastructure_id == infrastructure.id
    ).first()
    if not ins:
        ins = PropertyInfrastructureScore(
            property=property,
            infrastructure=infrastructure,
            score=score,
            distance=distance,
            walking_duration=walking_duration,
        )
        db.add(ins)
    return ins

def create_recommendation_property_infrastructure_score(
    db: Session,
    recommendation: Recommendation,
    property: Property,
    infrastructure: Infrastructure,
    score: float,
):
    ins = db.query(RecommendationPropertyInfrastructureScore).filter(
        RecommendationPropertyInfrastructureScore.recommendation_id == recommendation.id,
        RecommendationPropertyInfrastructureScore.property_id == property.id,
        RecommendationPropertyInfrastructureScore.infrastructure_id == infrastructure.id
    ).first()
    if not ins:
        ins = RecommendationPropertyInfrastructureScore(
            recommendation=recommendation,
            property=property,
            infrastructure=infrastructure,
            score=score,
        )
        db.add(ins)
    return ins

def create_recommendation_property_score(
    db: Session,
    recommendation: Recommendation,
    property: Property,
    score: float,
):
    ins = db.query(RecommendationPropertyScore).filter(
        RecommendationPropertyScore.recommendation_id == recommendation.id,
        RecommendationPropertyScore.property_id == property.id
    ).first()
    if not ins:
        ins = RecommendationPropertyScore(
            recommendation=recommendation,
            property=property,
            score=score,
        )
        db.add(ins)
    return ins


def main(db: Session, num_recommendations: int = DEFAULT_NUM_RECOMMENDATIONS):
    try:
        version = get_latest_version(db)
        user = get_or_create_guest_user(db)
        regions = db.query(Region).all()
        infra_types = db.query(InfrastructureType).all()
        infras = db.query(Infrastructure).all()
        properties = db.query(Property).all()

        last_suffix = db.query(Recommendation).filter(Recommendation.hash.like("seed_%")).count()
        run_with_progress(
            "시드 데이터 삽입 중...",
            num_recommendations,
            lambda idx: generate_seed(db, last_suffix + idx + 1,  user, regions, infra_types, infras, properties, version),
        )

        print(f"{num_recommendations}개의 시드 데이터가 생성되었습니다.")
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 2:
        usage()
        sys.exit(1)


    from app.database import SessionLocal
    db = SessionLocal()
    try:
        if len(sys.argv) == 2:
            main(db, int(sys.argv[1]))
        else:
            main(db)
    finally:
        db.close()
