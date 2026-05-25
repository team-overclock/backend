#!/usr/bin/with-contenv python3

import os
import sys
import random
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.enums import INFRASTRUCTURE_TYPE_VALUES
from app.redis import redis
from app.demo import create_guest_user
from app.crud.service import get_regions_by_depth
from app.models import (
    User,
    SearchLog,
    Recommendation,
    Infrastructure,
    Property,
    PropertyInfrastructure,
)

from scripts.common import SEED_TASK_ID_PREFIX, SEED_USERNAME_PREFIX, run_with_progress


DEFAULT_NUM_RECOMMENDATIONS = 30
DEFAULT_NUM_USERS = 0

start_ts = int(datetime(2022, 1, 1, 0, 0, 0).timestamp())
end_ts = int(datetime(2026, 12, 31, 23, 59, 59).timestamp())


def usage():
    print(f"사용법: python insert_seeds.py [생성할 추천 수] [생성할 사용자 수]")
    print(f"  - 데이터베이스 내 데이터를 기반으로 랜덤 추천 데이터를 생성하여 삽입합니다.")
    print(f"  - 생성할 추천 수 기본 값: {DEFAULT_NUM_RECOMMENDATIONS}")
    print(f"  - 생성할 사용자 수 기본 값: {DEFAULT_NUM_USERS}")


def random_range(min_value: int, max_value: int):
    results = random.sample(range(min_value, max_value + 1), k=2)
    min, max = sorted(results)
    return min, max


def get_or_create_guest_user(db: Session):
    """게스트 사용자 조회 및 생성"""
    return create_guest_user(db)[0]


def generate_seed_users(
    db: Session,
    suffix: int,
):
    name = f"{SEED_USERNAME_PREFIX}{suffix}"
    user = User(
        name=name,
        email=f"{name}@example.com",
        password="1234",
    )
    db.add(user)
    return user

def generate_seed_recommendations(
    db: Session,
    suffix: int,
    users: list[User],
    regions: list[dict],
    infra_types: list[str],
    infras: list[Infrastructure],
    properties: list[Property],
):
    n = min(5, len(users))
    max_request_users = random.choice([m for m in range(1, n + 1) for _ in range((n ** 2) - (m ** 2) + 1)])
    request_users = random.sample(users, k=max_request_users)

    selected_region = random.choice(regions)
    has_sale_price = random.choice([True, False])
    has_jeonse_price = random.choice([True, False])
    selected_sale_price = random_range(0, 999999999999) if has_sale_price else (None, None)
    selected_jeonse_price = random_range(0, 999999999999) if has_jeonse_price else (None, None)
    created_at, finished_at = random_range(start_ts, end_ts)
    created_at = datetime.fromtimestamp(created_at)
    failed_at = (created_at + timedelta(minutes=random.randint(1, 3))) if random.choice([True] + [False] * 4) else None
    finished_at = datetime.fromtimestamp(finished_at) if not failed_at and random.choice([True, False]) else None
    updated_at = finished_at + timedelta(minutes=random.randint(100, 1000)) if finished_at and random.choice([True, [False] * 4]) else None

    selected_infra_types = random.sample(infra_types, k=random.randint(1, len(infra_types)))
    random.shuffle(selected_infra_types)

    selected_properties = random.sample(properties, k=random.randint(5, 10))
    scores = [random.uniform(0.01, 100.0) for _ in selected_properties]
    selected_properties = sorted(selected_properties, key=lambda x: scores[selected_properties.index(x)], reverse=True)
    top_properties = [
        {
            "id": prop.id,
            "name": prop.name,
            "score": scores[selected_properties.index(prop)],
            "region": prop.region.name,
            "sale_price": sum(random_range(0, 999999999999))/2 if has_sale_price else None,
            "jeonse_price": sum(random_range(0, 999999999999))/2 if has_jeonse_price else None,
        }
        for prop in selected_properties[:5]
    ]

    rec = Recommendation(
        task_id=f"{SEED_TASK_ID_PREFIX}{suffix}",
        infrastructure_priorities=selected_infra_types,
        sale_price_min=selected_sale_price[0],
        sale_price_max=selected_sale_price[1],
        jeonse_price_min=selected_jeonse_price[0],
        jeonse_price_max=selected_jeonse_price[1],
        region=selected_region["name"],
        top_properties=top_properties,
        created_at=created_at,
        finished_at=finished_at,
        updated_at=updated_at,
        failed_at=failed_at,
    )
    db.add(rec)

    is_last_viewed = random.choice([True, False])
    last_viewed_at = rec.created_at + timedelta(minutes=random.randint(1, 1000)) if is_last_viewed else None
    search_logs = [
        SearchLog(
            task_id=rec.task_id,
            user=user,
            recommendation=rec,
            requested_at=rec.created_at,
            last_viewed_at=last_viewed_at,
            name=None if random.choice([True, False]) else f"추천 {'x' * random.randint(1, 10)}",
        )
        for user in request_users
    ]
    db.add_all(search_logs)

    for curr_property in selected_properties:
        for curr_infra in selected_infra_types:
            infra = random.choice(list(filter(lambda x: x.type.value == curr_infra, infras)))
            create_property_infrastructure_score(db, curr_property, infra, random.uniform(0.01, 100.0), random.randint(10, 1000))

    return rec

def create_property_infrastructure_score(
    db: Session,
    property: Property,
    infrastructure: Infrastructure,
    score: float,
    distance: int,
):
    ins = db.query(PropertyInfrastructure).filter(
        PropertyInfrastructure.property_id == property.id,
        PropertyInfrastructure.infrastructure_id == infrastructure.id
    ).first()
    if not ins:
        ins = PropertyInfrastructure(
            property=property,
            property_type=property.type,
            infrastructure=infrastructure,
            infrastructure_type=infrastructure.type.value,
            score=score,
            distance=distance,
        )
        db.add(ins)
    return ins


def main(db: Session, num_recommendations: int = DEFAULT_NUM_RECOMMENDATIONS, num_users: int = DEFAULT_NUM_USERS):
    guest_user = get_or_create_guest_user(db)
    regions = get_regions_by_depth(redis, 2)
    infra_types = INFRASTRUCTURE_TYPE_VALUES
    infras = db.query(Infrastructure).all()
    properties = db.query(Property).all()

    db_users = db.query(User).filter(User.name.like(f"{SEED_USERNAME_PREFIX}%")).all()
    last_user_suffix = len(db_users)
    last_task_id_suffix = db.query(Recommendation).filter(Recommendation.task_id.like(f"{SEED_TASK_ID_PREFIX}%")).count()

    new_users = run_with_progress(
        range(num_users),
        "시드 사용자 생성 중...",
        lambda idx, _: generate_seed_users(
            db,
            last_user_suffix + idx + 1,
        ),
    )

    users = [guest_user] + db_users + new_users
    run_with_progress(
        range(num_recommendations),
        "시드 데이터 삽입 중...",
        lambda idx, _: generate_seed_recommendations(
            db,
            last_task_id_suffix + idx + 1,
            users,
            regions,
            infra_types,
            infras, 
            properties,
        ),
    )

    return num_recommendations


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 3:
        usage()
        sys.exit(1)


    total = 0
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        num_recs = int(sys.argv[1]) if len(sys.argv) >= 2 else DEFAULT_NUM_RECOMMENDATIONS
        num_users = int(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_NUM_USERS
        total = main(db, num_recs, num_users)
    except Exception as e:
        db.rollback()
        raise e
    else:
        # db.rollback()
        db.commit()
        print(f"{total}개의 시드 데이터가 생성되었습니다.")
    finally:
        db.close()
